from pathlib import Path
import unittest

from spider_xhs import XhsApiError, XhsPcClient
from xhs_utils import xhs_util


def sample_raw_note(note_id="note-1"):
    return {
        "id": note_id,
        "note_card": {
            "type": "normal",
            "user": {
                "user_id": "user-1",
                "nickname": "tester",
                "avatar": "https://example.com/avatar.jpg",
            },
            "title": "Sample",
            "desc": "Desc",
            "interact_info": {
                "liked_count": "1",
                "collected_count": "2",
                "comment_count": "3",
                "share_count": "4",
            },
            "image_list": [
                {
                    "info_list": [
                        {"url": "https://example.com/small.jpg"},
                        {"url": "https://example.com/full.jpg"},
                    ]
                }
            ],
            "tag_list": [{"name": "tag"}],
            "time": 1710000000000,
            "ip_location": "Shanghai",
        },
    }


class FakeRawApi:
    def __init__(self):
        self.calls = []
        self.note_detail_calls = []
        self.fail_next_note = False

    def get_note_info(self, note_url, cookies, proxies):
        self.note_detail_calls.append((note_url, cookies, proxies))
        if self.fail_next_note:
            return False, "bad note", None
        return True, "success", {"data": {"items": [sample_raw_note()]}}

    def search_some_note(
        self,
        query,
        limit,
        cookies,
        sort_type_choice,
        note_type,
        note_time,
        note_range,
        pos_distance,
        geo,
        proxies,
    ):
        self.calls.append(("search", query, limit, cookies, proxies, geo))
        return True, "success", [
            {"model_type": "note", "id": "note-1", "xsec_token": "tok"},
            {"model_type": "user", "id": "user-1"},
        ]

    def get_note_all_comment(self, note_url, cookies, proxies):
        self.calls.append(("comments", note_url, cookies, proxies))
        return True, "success", [{"id": "comment-1"}]

    def get_homefeed_recommend_by_num(self, category, limit, cookies, proxies):
        self.calls.append(("homefeed", category, limit, cookies, proxies))
        return True, "success", [{"id": "note-2", "xsec_token": "tok2"}]

    def get_user_all_notes(self, user_url, cookies, proxies):
        self.calls.append(("user_notes", user_url, cookies, proxies))
        return True, "success", [{"note_id": "note-3", "xsec_token": "tok3"}]

    def get_unread_message(self, cookies, proxies):
        self.calls.append(("unread", cookies, proxies))
        return True, "success", {"data": {"count": 1}}

    def get_note_no_water_video(self, note_id):
        return True, "success", "https://example.com/video.mp4"

    def get_note_no_water_img(self, img_url):
        return False, "missing image", None


class XhsPcClientTest(unittest.TestCase):
    def test_injects_cookies_and_proxies_for_search(self):
        raw = FakeRawApi()
        client = XhsPcClient("cookie-string", proxies={"https": "proxy"}, raw_api=raw)

        result = client.search_notes("keyword", limit=10)

        self.assertEqual(result, [{"model_type": "note", "id": "note-1", "xsec_token": "tok"}])
        self.assertEqual(
            raw.calls[0],
            ("search", "keyword", 10, "cookie-string", {"https": "proxy"}, ""),
        )
        self.assertEqual(raw.note_detail_calls, [])

    def test_fetch_note_returns_normalized_note(self):
        raw = FakeRawApi()
        client = XhsPcClient("cookie-string", raw_api=raw)

        note = client.fetch_note("https://www.xiaohongshu.com/explore/note-1")

        self.assertEqual(note["note_id"], "note-1")
        self.assertEqual(note["note_type"], "图集")
        self.assertEqual(note["title"], "Sample")
        self.assertEqual(note["image_list"], ["https://example.com/full.jpg"])

    def test_search_with_detail_fetches_each_note(self):
        raw = FakeRawApi()
        client = XhsPcClient("cookie-string", raw_api=raw)

        notes = client.search_notes("keyword", limit=10, with_detail=True)

        self.assertEqual(len(notes), 1)
        self.assertIn("xsec_token=tok", raw.note_detail_calls[0][0])
        self.assertIn("xsec_source=pc_search", raw.note_detail_calls[0][0])

    def test_comments_use_configured_cookies(self):
        raw = FakeRawApi()
        client = XhsPcClient("cookie-string", proxies={"http": "proxy"}, raw_api=raw)

        comments = client.note_comments("note-url")

        self.assertEqual(comments, [{"id": "comment-1"}])
        self.assertEqual(raw.calls[0], ("comments", "note-url", "cookie-string", {"http": "proxy"}))

    def test_failed_calls_raise_facade_error(self):
        raw = FakeRawApi()
        client = XhsPcClient("cookie-string", raw_api=raw)

        with self.assertRaises(XhsApiError):
            client.no_watermark_image("bad-url")

    def test_raw_api_is_available(self):
        raw = FakeRawApi()
        client = XhsPcClient("cookie-string", raw_api=raw)

        self.assertIs(client.raw, raw)

    def test_static_assets_are_packaged_at_expected_path(self):
        static_dir = Path(xhs_util._STATIC_DIR)

        self.assertTrue((static_dir / "xhs_main_260411.js").exists())
        self.assertTrue((static_dir / "xhs_rap.js").exists())


if __name__ == "__main__":
    unittest.main()
