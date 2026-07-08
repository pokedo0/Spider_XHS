from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from loguru import logger

from xhs_utils.cookie_util import trans_cookies


_XYW_PATHS = {
    "/api/sns/web/v1/feed",
    "/api/sns/web/v1/homefeed",
    "/api/sns/web/v1/search/notes",
    "/api/sns/web/v1/search/usersearch",
    "/api/sns/web/v1/user_posted",
    "/api/sns/web/v1/user/otherinfo",
}

_XRAP_PATHS = {
    "/api/sns/web/v1/feed",
    "/api/sns/web/v1/homefeed",
    "/api/sns/web/v1/search/notes",
    "/api/sns/web/v1/search/usersearch",
}


def _load_xhshow():
    from xhshow import SessionManager, Xhshow
    from xhshow.core.xrap import x_rap_param

    return Xhshow, SessionManager, x_rap_param


class XhshowSigningAdapter:
    """PC signing adapter that preserves Spider_XHS helper return shapes."""

    def __init__(self, client=None, session_factory=None, x_rap_param_func=None):
        self.client = client
        self.session_factory = session_factory
        self.x_rap_param_func = x_rap_param_func
        self._sessions = {}
        self._lock = threading.Lock()

    def generate_request_params(
        self,
        cookies_str,
        api,
        data="",
        method="POST",
        legacy_generate_request_params=None,
        mode=None,
    ):
        mode = mode or os.getenv("SPIDER_XHS_SIGNER", "auto").strip().lower() or "auto"
        if mode not in {"auto", "xhshow", "legacy"}:
            logger.warning("Unknown SPIDER_XHS_SIGNER={}, using auto", mode)
            mode = "auto"

        if mode == "legacy":
            return self._call_legacy(
                legacy_generate_request_params,
                cookies_str,
                api,
                data,
                method,
            )

        try:
            return self._generate_with_xhshow(cookies_str, api, data, method)
        except Exception as exc:
            if mode == "xhshow" or legacy_generate_request_params is None:
                raise
            path, _ = self._split_api(api)
            logger.warning(
                "xhshow signing failed for method={} path={} error={}; falling back to legacy signer",
                method,
                path,
                exc,
            )
            return self._call_legacy(
                legacy_generate_request_params,
                cookies_str,
                api,
                data,
                method,
            )

    def generate_search_id(self, root_search_id=None, legacy_generate_search_id=None):
        if root_search_id:
            return root_search_id
        if self._mode() == "legacy":
            return legacy_generate_search_id(root_search_id) if legacy_generate_search_id else None
        try:
            return self._client().get_search_id()
        except Exception as exc:
            if legacy_generate_search_id is None:
                raise
            logger.warning("xhshow search_id failed: {}; falling back to legacy", exc)
            return legacy_generate_search_id(root_search_id)

    def generate_search_request_id(self, legacy_generate_search_request_id=None):
        if self._mode() == "legacy":
            return legacy_generate_search_request_id() if legacy_generate_search_request_id else None
        try:
            return self._client().get_search_request_id()
        except Exception as exc:
            if legacy_generate_search_request_id is None:
                raise
            logger.warning("xhshow search_request_id failed: {}; falling back to legacy", exc)
            return legacy_generate_search_request_id()

    def generate_x_b3_traceid(self, legacy_generate_x_b3_traceid=None):
        if self._mode() == "legacy":
            return legacy_generate_x_b3_traceid() if legacy_generate_x_b3_traceid else None
        try:
            return self._client().get_b3_trace_id()
        except Exception as exc:
            if legacy_generate_x_b3_traceid is None:
                raise
            logger.warning("xhshow x-b3-traceid failed: {}; falling back to legacy", exc)
            return legacy_generate_x_b3_traceid()

    def generate_xray_traceid(self, legacy_generate_xray_traceid=None):
        if self._mode() == "legacy":
            return legacy_generate_xray_traceid() if legacy_generate_xray_traceid else None
        try:
            return self._client().get_xray_trace_id()
        except Exception as exc:
            if legacy_generate_xray_traceid is None:
                raise
            logger.warning("xhshow x-xray-traceid failed: {}; falling back to legacy", exc)
            return legacy_generate_xray_traceid()

    def generate_x_rap_param(self, api, data, app_id=None, legacy_generate_x_rap_param=None):
        if self._mode() == "legacy":
            return self._call_legacy_xrap(legacy_generate_x_rap_param, api, data, app_id)
        try:
            path, _ = self._split_api(api)
            rap_api = api if str(api).startswith("//") else f"//edith.xiaohongshu.com{path}"
            return self._x_rap_param()(rap_api, data or {})
        except Exception as exc:
            if legacy_generate_x_rap_param is None:
                raise
            logger.warning("xhshow x-rap-param failed: {}; falling back to legacy", exc)
            return self._call_legacy_xrap(legacy_generate_x_rap_param, api, data, app_id)

    def _generate_with_xhshow(self, cookies_str, api, data, method):
        client = self._client()
        method = method.upper()
        cookies = trans_cookies(cookies_str)
        path, params = self._split_api(api)
        sign_format = self._sign_format(path)
        x_rap = self._needs_xrap(path)
        session = self._session_for(cookies) if sign_format == "xys" else None
        body = self._compact_body(data)

        if method == "GET":
            headers = client.sign_headers_get(
                uri=path,
                cookies=cookies,
                params=params,
                session=session,
                sign_format=sign_format,
                x_rap=x_rap,
            )
        elif method == "POST":
            payload = data if isinstance(data, dict) else self._json_payload(data)
            headers = client.sign_headers_post(
                uri=path,
                cookies=cookies,
                payload=payload,
                session=session,
                sign_format=sign_format,
                x_rap=x_rap,
            )
        else:
            raise ValueError(f"Unsupported method: {method}")

        logger.trace(
            "Generated PC headers with xhshow method={} path={} sign_format={} x_rap={} session_key={}",
            method,
            path,
            sign_format,
            x_rap,
            self._safe_session_key(cookies),
        )
        return headers, cookies, body

    def _client(self):
        if self.client is None:
            Xhshow, _, _ = _load_xhshow()
            self.client = Xhshow()
        return self.client

    def _session_factory(self):
        if self.session_factory is None:
            _, SessionManager, _ = _load_xhshow()
            self.session_factory = SessionManager
        return self.session_factory

    def _x_rap_param(self):
        if self.x_rap_param_func is None:
            _, _, x_rap_param = _load_xhshow()
            self.x_rap_param_func = x_rap_param
        return self.x_rap_param_func

    def _session_for(self, cookies):
        key = self._safe_session_key(cookies)
        with self._lock:
            if key not in self._sessions:
                self._sessions[key] = self._session_factory()()
            return self._sessions[key]

    @staticmethod
    def _split_api(api):
        parsed = urlsplit(api)
        path = parsed.path or api.split("?", 1)[0]
        query = parsed.query if parsed.query else (api.split("?", 1)[1] if "?" in api else "")
        params = {
            key: value
            for key, value in parse_qsl(query, keep_blank_values=True)
        }
        return path, params

    @staticmethod
    def _compact_body(data):
        if isinstance(data, (dict, list)):
            return json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return data or ""

    @staticmethod
    def _json_payload(data):
        if not data:
            return None
        if isinstance(data, str):
            return json.loads(data)
        return data

    @staticmethod
    def _sign_format(path):
        return "xyw" if path in _XYW_PATHS else "xys"

    @staticmethod
    def _needs_xrap(path):
        return path in _XRAP_PATHS

    @staticmethod
    def _safe_session_key(cookies):
        raw = cookies.get("a1") or cookies.get("web_session") or "anonymous"
        return hashlib.sha256(str(raw).encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _call_legacy(legacy_generate_request_params, cookies_str, api, data, method):
        if legacy_generate_request_params is None:
            raise RuntimeError("legacy_generate_request_params is required")
        return legacy_generate_request_params(cookies_str, api, data, method)

    @staticmethod
    def _call_legacy_xrap(legacy_generate_x_rap_param, api, data, app_id):
        if legacy_generate_x_rap_param is None:
            raise RuntimeError("legacy_generate_x_rap_param is required")
        return legacy_generate_x_rap_param(api, data, app_id)

    @staticmethod
    def _mode():
        mode = os.getenv("SPIDER_XHS_SIGNER", "auto").strip().lower() or "auto"
        return mode if mode in {"auto", "xhshow", "legacy"} else "auto"
