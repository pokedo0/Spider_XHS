from urllib.parse import urlencode

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.data_util import handle_note_info

from spider_xhs.errors import XhsApiError


class XhsPcClient:
    """Cookie-authenticated facade for Spider_XHS PC crawling APIs."""

    def __init__(self, cookies, proxies=None, raw_api=None):
        if not cookies or not str(cookies).strip():
            raise ValueError("cookies must be a non-empty cookie string")
        self.cookies = cookies
        self.proxies = proxies
        self._owns_raw = raw_api is None
        self.raw = raw_api if raw_api is not None else XHS_Apis()

    def close(self):
        if not self._owns_raw:
            return
        close = getattr(self.raw, "close", None)
        if callable(close):
            close()

    def export_cookies(self):
        export = getattr(self.raw, "export_cookies", None)
        if callable(export):
            return export()
        return str(self.cookies)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def homefeed_channels(self):
        return self._unwrap(
            self.raw.get_homefeed_all_channel(self.cookies, self.proxies),
            "homefeed_channels",
        )

    def homefeed_notes(self, category, limit=20, with_detail=False):
        items = self._unwrap(
            self.raw.get_homefeed_recommend_by_num(
                category,
                limit,
                self.cookies,
                self.proxies,
            ),
            "homefeed_notes",
        )
        items = self._limit(items, limit)
        if not with_detail:
            return items
        return self._fetch_item_details(items, default_xsec_source="pc_feed")

    def user_info(self, user_id):
        return self._unwrap(
            self.raw.get_user_info(user_id, self.cookies, self.proxies),
            "user_info",
        )

    def self_info(self, version=2):
        if version == 1:
            result = self.raw.get_user_self_info(self.cookies, self.proxies)
        else:
            result = self.raw.get_user_self_info2(self.cookies, self.proxies)
        return self._unwrap(result, "self_info")

    def user_notes(self, user_url, limit=None, with_detail=False):
        items = self._unwrap(
            self.raw.get_user_all_notes(user_url, self.cookies, self.proxies),
            "user_notes",
        )
        items = self._limit(items, limit)
        if not with_detail:
            return items
        return self._fetch_item_details(items, default_xsec_source="pc_user")

    def user_like_notes(self, user_url, limit=None, with_detail=False):
        items = self._unwrap(
            self.raw.get_user_all_like_note_info(
                user_url,
                self.cookies,
                self.proxies,
            ),
            "user_like_notes",
        )
        items = self._limit(items, limit)
        if not with_detail:
            return items
        return self._fetch_item_details(items, default_xsec_source="pc_user")

    def user_collect_notes(self, user_url, limit=None, with_detail=False):
        items = self._unwrap(
            self.raw.get_user_all_collect_note_info(
                user_url,
                self.cookies,
                self.proxies,
            ),
            "user_collect_notes",
        )
        items = self._limit(items, limit)
        if not with_detail:
            return items
        return self._fetch_item_details(items, default_xsec_source="pc_search")

    def fetch_note(self, note_url):
        res_json = self._unwrap(
            self.raw.get_note_info(note_url, self.cookies, self.proxies),
            "fetch_note",
        )
        items = (res_json.get("data") or {}).get("items") or []
        if not items:
            raise XhsApiError("fetch_note", "response has no note items")
        return self._normalize_note(items[0], note_url, "fetch_note")

    def fetch_notes(self, note_urls, skip_errors=False):
        notes = []
        for note_url in note_urls:
            try:
                notes.append(self.fetch_note(note_url))
            except XhsApiError:
                if not skip_errors:
                    raise
        return notes

    def search_keywords(self, word):
        return self._unwrap(
            self.raw.get_search_keyword(word, self.cookies, self.proxies),
            "search_keywords",
        )

    def search_notes(
        self,
        query,
        limit=20,
        sort_type_choice=0,
        note_type=0,
        note_time=0,
        note_range=0,
        pos_distance=0,
        geo=None,
        with_detail=False,
    ):
        items = self._unwrap(
            self.raw.search_some_note(
                query,
                limit,
                self.cookies,
                sort_type_choice,
                note_type,
                note_time,
                note_range,
                pos_distance,
                geo or "",
                self.proxies,
            ),
            "search_notes",
        )
        notes = [
            item for item in items
            if not isinstance(item, dict) or item.get("model_type", "note") == "note"
        ]
        notes = self._limit(notes, limit)
        if not with_detail:
            return notes
        return self._fetch_item_details(notes, default_xsec_source="pc_search")

    def search_users(self, query, limit=20):
        return self._unwrap(
            self.raw.search_some_user(query, limit, self.cookies, self.proxies),
            "search_users",
        )

    def note_comments(self, note_url):
        return self._unwrap(
            self.raw.get_note_all_comment(note_url, self.cookies, self.proxies),
            "note_comments",
        )

    def unread_message(self):
        return self._unwrap(
            self.raw.get_unread_message(self.cookies, self.proxies),
            "unread_message",
        )

    def mentions(self):
        return self._unwrap(
            self.raw.get_all_metions(self.cookies, self.proxies),
            "mentions",
        )

    def likes_and_collects(self):
        return self._unwrap(
            self.raw.get_all_likesAndcollects(self.cookies, self.proxies),
            "likes_and_collects",
        )

    def new_connections(self):
        return self._unwrap(
            self.raw.get_all_new_connections(self.cookies, self.proxies),
            "new_connections",
        )

    def no_watermark_video(self, note_id):
        return self._unwrap(
            self.raw.get_note_no_water_video(note_id),
            "no_watermark_video",
        )

    def no_watermark_image(self, img_url):
        return self._unwrap(
            self.raw.get_note_no_water_img(img_url),
            "no_watermark_image",
        )

    def note_url_from_item(self, item, default_xsec_source="pc_search"):
        note_id = item.get("note_id") or item.get("id") or item.get("source_note_id")
        if not note_id:
            raise XhsApiError("note_url_from_item", "note item is missing note id")

        params = {}
        xsec_token = item.get("xsec_token")
        if xsec_token:
            params["xsec_token"] = xsec_token
        xsec_source = item.get("xsec_source") or default_xsec_source
        if xsec_source:
            params["xsec_source"] = xsec_source

        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url

    def _fetch_item_details(self, items, default_xsec_source):
        note_urls = [
            self.note_url_from_item(item, default_xsec_source)
            for item in items
        ]
        return self.fetch_notes(note_urls)

    def _normalize_note(self, raw_note, note_url, operation):
        note = dict(raw_note)
        note["url"] = note_url
        try:
            return handle_note_info(note)
        except Exception as exc:
            raise XhsApiError(operation, exc) from exc

    @staticmethod
    def _limit(items, limit):
        if limit is None:
            return list(items)
        return list(items)[:limit]

    @staticmethod
    def _unwrap(result, operation):
        success, msg, data = result
        if not success:
            code = data.get("code") if isinstance(data, dict) else None
            raise XhsApiError(operation, msg, code=code, response=data)
        return data
