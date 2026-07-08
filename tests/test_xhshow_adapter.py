import json
import os
import unittest

from xhs_utils.cookie_util import trans_cookies


class FakeSession:
    next_id = 1

    def __init__(self):
        self.id = FakeSession.next_id
        FakeSession.next_id += 1


class FakeXhshow:
    def __init__(self):
        self.calls = []

    def sign_headers_get(self, **kwargs):
        self.calls.append(("GET", kwargs))
        return {
            "x-s": f"{kwargs['sign_format'].upper()}_sig",
            "x-s-common": "common",
            "x-t": "123",
            "x-b3-traceid": "b3",
            "x-xray-traceid": "xray",
            "xy-direction": "42",
        }

    def sign_headers_post(self, **kwargs):
        self.calls.append(("POST", kwargs))
        headers = {
            "x-s": f"{kwargs['sign_format'].upper()}_sig",
            "x-s-common": "common",
            "x-t": "123",
            "x-b3-traceid": "b3",
            "x-xray-traceid": "xray",
            "xy-direction": "42",
        }
        if kwargs.get("x_rap"):
            headers["x-rap-param"] = "rap-from-xhshow"
        return headers

    def get_search_id(self):
        return "xhshow-search-id"

    def get_search_request_id(self):
        return "123456-1700000000000"

    def get_b3_trace_id(self):
        return "b3trace"

    def get_xray_trace_id(self):
        return "xraytrace"


class XhshowAdapterTest(unittest.TestCase):
    def setUp(self):
        from xhs_utils.xhshow_adapter import XhshowSigningAdapter

        FakeSession.next_id = 1
        self.client = FakeXhshow()
        self.adapter = XhshowSigningAdapter(
            client=self.client,
            session_factory=FakeSession,
        )
        os.environ.pop("SPIDER_XHS_SIGNER", None)

    def test_get_with_query_is_split_into_path_and_params(self):
        headers, cookies, body = self.adapter.generate_request_params(
            "a1=A; web_session=S",
            "/api/sns/web/v1/user_posted?num=30&cursor=&image_formats=jpg%2Cwebp%2Cavif",
            "",
            "GET",
        )

        method, call = self.client.calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(call["uri"], "/api/sns/web/v1/user_posted")
        self.assertEqual(
            call["params"],
            {"num": "30", "cursor": "", "image_formats": "jpg,webp,avif"},
        )
        self.assertEqual(call["sign_format"], "xyw")
        self.assertIsNone(call["session"])
        self.assertEqual(cookies, trans_cookies("a1=A; web_session=S"))
        self.assertEqual(body, "")
        self.assertEqual(headers["x-s"], "XYW_sig")

    def test_post_body_is_compact_json_and_feed_gets_xrap(self):
        payload = {"source_note_id": "n1", "image_formats": ["jpg", "webp"]}

        headers, _, body = self.adapter.generate_request_params(
            "a1=A; web_session=S",
            "/api/sns/web/v1/feed",
            payload,
            "POST",
        )

        method, call = self.client.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(call["uri"], "/api/sns/web/v1/feed")
        self.assertEqual(call["payload"], payload)
        self.assertEqual(call["sign_format"], "xyw")
        self.assertTrue(call["x_rap"])
        self.assertEqual(body, json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
        self.assertEqual(headers["x-rap-param"], "rap-from-xhshow")

    def test_comments_use_xys_with_reused_session_per_cookie(self):
        api = "/api/sns/web/v2/comment/page?note_id=n1&cursor="

        self.adapter.generate_request_params("a1=A; web_session=S", api, "", "GET")
        self.adapter.generate_request_params("a1=A; web_session=S", api, "", "GET")
        self.adapter.generate_request_params("a1=B; web_session=T", api, "", "GET")

        first = self.client.calls[0][1]
        second = self.client.calls[1][1]
        third = self.client.calls[2][1]
        self.assertEqual(first["sign_format"], "xys")
        self.assertIs(first["session"], second["session"])
        self.assertIsNot(first["session"], third["session"])

    def test_xrap_only_for_targeted_endpoints(self):
        self.adapter.generate_request_params(
            "a1=A; web_session=S",
            "/api/sns/web/v1/search/recommend?keyword=x",
            "",
            "GET",
        )
        self.adapter.generate_request_params(
            "a1=A; web_session=S",
            "/api/sns/web/v1/search/notes",
            {"keyword": "x"},
            "POST",
        )

        self.assertFalse(self.client.calls[0][1]["x_rap"])
        self.assertTrue(self.client.calls[1][1]["x_rap"])

    def test_fallback_preserves_legacy_return_shape(self):
        legacy_calls = []

        def legacy(cookies_str, api, data, method):
            legacy_calls.append((cookies_str, api, data, method))
            return {"x-s": "legacy"}, {"a1": "A"}, "legacy-body"

        headers, cookies, body = self.adapter.generate_request_params(
            "a1=A",
            "/api/sns/web/v1/feed",
            {"x": 1},
            "POST",
            legacy_generate_request_params=legacy,
            mode="legacy",
        )

        self.assertEqual(headers, {"x-s": "legacy"})
        self.assertEqual(cookies, {"a1": "A"})
        self.assertEqual(body, "legacy-body")
        self.assertEqual(legacy_calls, [("a1=A", "/api/sns/web/v1/feed", {"x": 1}, "POST")])

    def test_search_id_wrappers_use_xhshow_but_preserve_root_id(self):
        self.assertEqual(self.adapter.generate_search_id(), "xhshow-search-id")
        self.assertEqual(self.adapter.generate_search_id("root"), "root")
        self.assertEqual(self.adapter.generate_search_request_id(), "123456-1700000000000")


if __name__ == "__main__":
    unittest.main()
