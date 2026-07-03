import unittest
from unittest.mock import patch

from xhs_utils import http_client


class FakeTransport:
    def __init__(self):
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return {"ok": True}


class HttpClientTest(unittest.TestCase):
    def test_headers_force_default_headers_false_and_preserve_kwargs(self):
        transport = FakeTransport()
        headers = {"origin": "https://creator.xiaohongshu.com", "x-s": "sig"}
        cookies = {"a1": "cookie"}
        proxies = {"https": "http://proxy"}

        with patch.object(http_client, "_transport", return_value=transport):
            result = http_client.get(
                "https://example.com/api",
                headers=headers,
                cookies=cookies,
                proxies=proxies,
                timeout=10,
                params={"page": "1"},
            )

        self.assertEqual(result, {"ok": True})
        method, url, kwargs = transport.calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(url, "https://example.com/api")
        self.assertIs(kwargs["headers"], headers)
        self.assertIs(kwargs["cookies"], cookies)
        self.assertIs(kwargs["proxies"], proxies)
        self.assertEqual(kwargs["timeout"], 10)
        self.assertEqual(kwargs["params"], {"page": "1"})
        self.assertEqual(kwargs["impersonate"], "chrome")
        self.assertIs(kwargs["default_headers"], False)

    def test_without_headers_does_not_force_default_headers_false(self):
        transport = FakeTransport()

        with patch.object(http_client, "_transport", return_value=transport):
            http_client.post(
                "https://example.com/media",
                data=b"body",
                stream=True,
                timeout=10,
            )

        method, _, kwargs = transport.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(kwargs["data"], b"body")
        self.assertIs(kwargs["stream"], True)
        self.assertEqual(kwargs["impersonate"], "chrome")
        self.assertNotIn("default_headers", kwargs)


if __name__ == "__main__":
    unittest.main()
