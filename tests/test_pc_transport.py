import unittest
from unittest.mock import Mock, patch

from apis.xhs_pc_apis import XHS_Apis, _parse_response, _sanitize_error_message
from spider_xhs import XhsApiError, XhsPcClient
from xhs_utils.http_client import (
    PC_ACCEPT_ENCODING,
    PC_IMPERSONATE,
    PC_SEC_CH_UA,
    PC_USER_AGENT,
    PcHttpSession,
)
from xhs_utils.xhs_util import generate_request_params, get_common_headers, get_request_headers_template


class FakeCookies:
    def __init__(self):
        self.values = {}

    def set(self, name, value, **kwargs):
        self.values[name] = value

    def get_dict(self):
        return dict(self.values)


class FakeCurlSession:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.cookies = FakeCookies()
        self.requests = []
        self.closed = False
        self.response = FakeResponse({"success": True, "data": {}})
        self.__class__.instances.append(self)

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return self.response

    def close(self):
        self.closed = True


class FakeResponse:
    def __init__(self, payload=None, status_code=200, url="https://edith.xiaohongshu.com/api/test", json_error=None):
        self.payload = payload
        self.status_code = status_code
        self.url = url
        self.json_error = json_error

    def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class FakeHttpSession:
    def __init__(self):
        self.prepared = []
        self.request_kwargs = None
        self.closed = False
        self.cookies = "a1=A; web_session=NEW; gid=G"
        self.response = FakeResponse({"success": True, "data": {"ok": True}})

    def prepare_cookies(self, cookies):
        self.prepared.append(cookies)
        return self.cookies

    def get(self, url, **kwargs):
        self.request_kwargs = kwargs
        return self.response

    def export_cookies(self):
        return self.cookies

    def close(self):
        self.closed = True


class PcProfileTest(unittest.TestCase):
    def test_api_and_navigation_headers_use_windows_chrome_146(self):
        api_headers = get_request_headers_template()
        page_headers = get_common_headers()

        for headers in (api_headers, page_headers):
            self.assertEqual(headers["user-agent"], PC_USER_AGENT)
            self.assertEqual(headers["sec-ch-ua"], PC_SEC_CH_UA)
            self.assertEqual(headers["sec-ch-ua-platform"], '"Windows"')
            self.assertEqual(headers["accept-encoding"], PC_ACCEPT_ENCODING)
            self.assertNotIn("authority", headers)

    def test_xhshow_signatures_are_merged_with_complete_api_headers(self):
        signed = {
            "x-s": "signed",
            "x-t": "123",
            "x-s-common": "common",
            "x-b3-traceid": "b3",
            "x-xray-traceid": "xray",
        }
        with patch(
            "xhs_utils.xhs_util._XHSHOW_ADAPTER.generate_request_params",
            return_value=(signed, {"a1": "A"}, ""),
        ):
            headers, cookies, body = generate_request_params("a1=A", "/api/test", "", "GET")

        self.assertEqual(headers["user-agent"], PC_USER_AGENT)
        self.assertEqual(headers["x-s"], "signed")
        self.assertEqual(headers["x-xray-traceid"], "xray")
        self.assertEqual(cookies, {"a1": "A"})
        self.assertEqual(body, "")


class PcHttpSessionTest(unittest.TestCase):
    def test_empty_cookie_is_rejected_before_signing_or_request(self):
        session = PcHttpSession(session_factory=FakeCurlSession)

        with self.assertRaisesRegex(ValueError, "non-empty"):
            session.prepare_cookies("")

    def setUp(self):
        FakeCurlSession.instances = []

    def test_server_cookie_update_survives_repeated_original_cookie(self):
        transport = PcHttpSession(session_factory=FakeCurlSession)
        transport.prepare_cookies("a1=A; web_session=OLD")
        first_session = FakeCurlSession.instances[0]
        first_session.cookies.set("web_session", "NEW")
        first_session.cookies.set("gid", "G")

        current = transport.prepare_cookies("a1=A; web_session=OLD")

        self.assertIs(transport._session, first_session)
        self.assertIn("web_session=NEW", current)
        self.assertIn("gid=G", current)

    def test_different_caller_cookie_replaces_session(self):
        transport = PcHttpSession(session_factory=FakeCurlSession)
        transport.prepare_cookies("a1=A; web_session=ONE")
        first_session = FakeCurlSession.instances[0]

        current = transport.prepare_cookies("a1=B; web_session=TWO")

        self.assertTrue(first_session.closed)
        self.assertEqual(len(FakeCurlSession.instances), 2)
        self.assertIn("a1=B", current)
        self.assertNotIn("a1=A", current)

    def test_request_uses_fixed_profile_and_never_forwards_original_cookies(self):
        transport = PcHttpSession(session_factory=FakeCurlSession)
        transport.prepare_cookies("a1=A")

        transport.get("https://edith.xiaohongshu.com/api/test", cookies={"a1": "OLD"})

        session = FakeCurlSession.instances[0]
        self.assertEqual(session.kwargs["impersonate"], PC_IMPERSONATE)
        request_kwargs = session.requests[0][2]
        self.assertNotIn("cookies", request_kwargs)
        self.assertFalse(request_kwargs["default_headers"])
        self.assertEqual(request_kwargs["accept_encoding"], PC_ACCEPT_ENCODING)


class PcApiResponseTest(unittest.TestCase):
    def test_unexpected_error_message_redacts_cookie_and_signature_values(self):
        message = _sanitize_error_message(
            RuntimeError(
                "Cookie: a1=secret; web_session=session-secret "
                "xsec_token=query-secret x-s=signature-secret"
            )
        )

        self.assertNotIn("secret", message)
        self.assertIn("Cookie: <redacted>", message)
        self.assertIn("web_session=<redacted>", message)
        self.assertIn("xsec_token=<redacted>", message)
        self.assertIn("x-s=<redacted>", message)

    def test_missing_msg_uses_alternative_message_and_code(self):
        success, msg, payload = _parse_response(
            FakeResponse({"success": False, "code": 300012, "message": "request blocked"})
        )

        self.assertFalse(success)
        self.assertIn("request blocked", msg)
        self.assertIn("code=300012", msg)
        self.assertEqual(payload["code"], 300012)

    def test_non_json_response_is_sanitized(self):
        success, msg, payload = _parse_response(
            FakeResponse(status_code=503, json_error=ValueError("secret body"))
        )

        self.assertFalse(success)
        self.assertIn("http_status=503", msg)
        self.assertNotIn("secret body", msg)
        self.assertIsNone(payload)

    def test_raw_api_signs_with_effective_session_cookies(self):
        http = FakeHttpSession()
        api = XHS_Apis(http_session=http)
        captured = {}

        def fake_generate(cookies, path, data, method):
            captured["cookies"] = cookies
            return {"x-s": "sig"}, {}, ""

        with patch("apis.xhs_pc_apis.generate_request_params", side_effect=fake_generate):
            success, _, data = api.get_homefeed_all_channel("a1=A; web_session=OLD")

        self.assertTrue(success)
        self.assertEqual(data, {"success": True, "data": {"ok": True}})
        self.assertEqual(captured["cookies"], http.cookies)
        self.assertNotIn("cookies", http.request_kwargs)


class PcFacadeLifecycleTest(unittest.TestCase):
    def test_owned_raw_api_is_closed_and_exports_current_cookies(self):
        raw = Mock()
        raw.export_cookies.return_value = "a1=A; web_session=NEW"
        with patch("spider_xhs.pc.XHS_Apis", return_value=raw):
            with XhsPcClient("a1=A") as client:
                self.assertEqual(client.export_cookies(), "a1=A; web_session=NEW")

        raw.close.assert_called_once_with()

    def test_injected_raw_api_is_not_closed(self):
        raw = unittest.mock.Mock()
        client = XhsPcClient("a1=A", raw_api=raw)

        client.close()

        raw.close.assert_not_called()

    def test_error_exposes_code_and_response(self):
        raw = unittest.mock.Mock()
        raw.get_note_no_water_img.return_value = (
            False,
            "request blocked",
            {"code": 300012},
        )
        client = XhsPcClient("a1=A", raw_api=raw)

        with self.assertRaises(XhsApiError) as raised:
            client.no_watermark_image("bad")

        self.assertEqual(raised.exception.code, 300012)
        self.assertEqual(raised.exception.response, {"code": 300012})


if __name__ == "__main__":
    unittest.main()
