"""
集成测试：验证改动后的视频选流和下载逻辑能正确工作。

调用顺序：
  1. XhsPcClient.raw.get_note_info()  → 拿到原始 API 数据
  2. pick_best_video_stream()          → H.265 优先 + avg_bitrate 最高
  3. download_media()                  → backup_url 优先，失败再用 master_url

运行方式（在项目根目录）：
  python -m pytest tests/test_video_download.py -v -s
  或
  python tests/test_video_download.py
"""

import os
import tempfile
import unittest

from dotenv import load_dotenv

from spider_xhs import XhsPcClient
from xhs_utils.data_util import download_media, pick_best_video_stream


# ---------------------------------------------------------------------------
# 辅助：构造只包含指定流的 video_info dict
# ---------------------------------------------------------------------------

def make_video_info(h265=None, h264=None):
    return {
        "media": {
            "stream": {
                "h265": h265 or [],
                "h264": h264 or [],
            }
        }
    }


def make_stream(avg_bitrate, backup_url="http://bak.example.com/v.mp4",
                master_url="http://master.example.com/v.mp4?sign=xxx"):
    return {
        "avg_bitrate": avg_bitrate,
        "backup_urls": [backup_url],
        "master_url": master_url,
    }


# ---------------------------------------------------------------------------
# 单元测试：pick_best_video_stream 逻辑
# ---------------------------------------------------------------------------

class TestPickBestVideoStream(unittest.TestCase):

    def test_prefer_h265_over_h264(self):
        """H.265 存在时，即使 avg_bitrate 更低也应优先。"""
        video_info = make_video_info(
            h265=[make_stream(1_000_000, backup_url="http://bak/h265.mp4")],
            h264=[make_stream(5_000_000, backup_url="http://bak/h264.mp4")],
        )
        backup, master = pick_best_video_stream(video_info)
        self.assertEqual(backup, "http://bak/h265.mp4")

    def test_h265_selects_highest_avg_bitrate(self):
        """H.265 多路流时取 avg_bitrate 最大的。"""
        video_info = make_video_info(h265=[
            make_stream(1_000_000, backup_url="http://bak/low.mp4"),
            make_stream(4_500_000, backup_url="http://bak/uhd.mp4"),  # 最高
            make_stream(1_900_000, backup_url="http://bak/mid.mp4"),
        ])
        backup, _ = pick_best_video_stream(video_info)
        self.assertEqual(backup, "http://bak/uhd.mp4")

    def test_fallback_to_h264_when_no_h265(self):
        """H.265 为空时应回退到 H.264。"""
        video_info = make_video_info(
            h265=[],
            h264=[
                make_stream(1_000_000, backup_url="http://bak/low264.mp4"),
                make_stream(3_000_000, backup_url="http://bak/high264.mp4"),
            ],
        )
        backup, _ = pick_best_video_stream(video_info)
        self.assertEqual(backup, "http://bak/high264.mp4")

    def test_returns_none_when_no_streams(self):
        """完全没有流时返回 (None, None)。"""
        backup, master = pick_best_video_stream(make_video_info())
        self.assertIsNone(backup)
        self.assertIsNone(master)

    def test_backup_and_master_are_separate(self):
        """backup_url 和 master_url 应该分别返回。"""
        video_info = make_video_info(h265=[
            make_stream(2_000_000,
                        backup_url="http://bak/v.mp4",
                        master_url="http://master/v.mp4?sign=abc"),
        ])
        backup, master = pick_best_video_stream(video_info)
        self.assertEqual(backup, "http://bak/v.mp4")
        self.assertEqual(master, "http://master/v.mp4?sign=abc")


# ---------------------------------------------------------------------------
# 集成测试：实际网络请求 + 下载（需要 .env 中的 COOKIES）
# ---------------------------------------------------------------------------

NOTE_URL = (
    "https://www.xiaohongshu.com/explore/6937d509000000001d039d86"
    "?xsec_token=ABMGyWGuvzh-GyYLC8NxHLWdGXeSLb8tcg0WpXGJeftko="
    "&xsec_source=pc_search&source=web_explore_feed"
)


class TestVideoDownloadIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_dotenv()
        cls.cookies = os.getenv("COOKIES", "")

    def _skip_if_no_cookies(self):
        if not self.cookies:
            self.skipTest("COOKIES not set in .env — skipping integration test")

    def test_pick_best_stream_from_real_api(self):
        """验证真实 API 返回数据中能正确选出最高码率的 H.265 流。"""
        self._skip_if_no_cookies()

        client = XhsPcClient(cookies=self.cookies)
        success, msg, data = client.raw.get_note_info(NOTE_URL, self.cookies, proxies=None)
        self.assertTrue(success, f"API 调用失败: {msg}")

        items = data.get("data", {}).get("items", [])
        self.assertTrue(items, "API 返回空 items")

        note_card = items[0]["note_card"]
        self.assertEqual(note_card["type"], "video", "笔记类型不是视频")

        video_info = note_card.get("video", {})
        backup_url, master_url = pick_best_video_stream(video_info)

        self.assertIsNotNone(backup_url or master_url, "未能提取到任何视频链接")
        print(f"\n[选出的视频流]")
        print(f"  backup_url : {backup_url}")
        print(f"  master_url : {master_url}")

        # 验证 backup_url 是 H.265 / UHD（码率最高）
        # 根据 raw_data.json，最高码率的 H.265 流的 backup_url 包含 "_226.mp4"
        if backup_url:
            self.assertIn("sns-bak", backup_url,
                          "backup_url 应该来自 sns-bak 域名（无鉴权链接）")

    def test_download_video_to_temp_dir(self):
        """
        真实下载视频（约 71MB UHD H.265），先试 backup_url，失败再试 master_url。
        该测试会发起实际 HTTP 下载，完成后检查文件存在且大小 > 0。
        """
        self._skip_if_no_cookies()

        client = XhsPcClient(cookies=self.cookies)
        success, msg, data = client.raw.get_note_info(NOTE_URL, self.cookies, proxies=None)
        self.assertTrue(success, f"API 调用失败: {msg}")

        items = data.get("data", {}).get("items", [])
        note_card = items[0]["note_card"]
        video_info = note_card.get("video", {})
        backup_url, master_url = pick_best_video_stream(video_info)

        self.assertIsNotNone(backup_url or master_url, "没有可用的视频链接")

        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"\n[开始下载到临时目录] {tmpdir}")
            print(f"  主链接 (backup): {backup_url}")
            print(f"  备用链接 (master): {master_url}")

            download_media(
                path=tmpdir,
                name="test_video",
                url=backup_url,
                type="video",
                fallback_url=master_url,
            )

            import pathlib
            video_file = pathlib.Path(tmpdir) / "test_video.mp4"
            self.assertTrue(video_file.exists(), "视频文件未生成")
            size_mb = video_file.stat().st_size / (1024 * 1024)
            print(f"  下载完成，文件大小: {size_mb:.2f} MB")
            self.assertGreater(size_mb, 1.0, "下载的视频文件过小，可能下载失败")


if __name__ == "__main__":
    unittest.main(verbosity=2)
