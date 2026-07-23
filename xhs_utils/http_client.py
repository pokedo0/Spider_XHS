from __future__ import annotations

import hashlib
import threading
from time import perf_counter
from typing import Any
from urllib.parse import urlsplit

from loguru import logger

from xhs_utils.cookie_util import trans_cookies


DEFAULT_IMPERSONATE = "chrome"
PC_CHROME_VERSION = "146"
PC_IMPERSONATE = f"chrome{PC_CHROME_VERSION}"
PC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{PC_CHROME_VERSION}.0.0.0 Safari/537.36"
)
PC_SEC_CH_UA = (
    f'"Chromium";v="{PC_CHROME_VERSION}", '
    '"Not-A.Brand";v="24", '
    f'"Google Chrome";v="{PC_CHROME_VERSION}"'
)
PC_ACCEPT_ENCODING = "gzip, deflate, br, zstd"
_COOKIE_DOMAIN = ".xiaohongshu.com"


def _transport():
    try:
        from curl_cffi import requests as curl_requests
    except ModuleNotFoundError as exc:
        raise RuntimeError("curl_cffi is required for Spider_XHS HTTP requests") from exc
    return curl_requests


def _request_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    request_kwargs = dict(kwargs)
    request_kwargs.setdefault("impersonate", DEFAULT_IMPERSONATE)
    if request_kwargs.get("headers") is not None:
        request_kwargs["default_headers"] = False
    return request_kwargs


def request(method: str, url: str, **kwargs: Any):
    return _transport().request(method, url, **_request_kwargs(kwargs))


def get(url: str, **kwargs: Any):
    return request("GET", url, **kwargs)


def post(url: str, **kwargs: Any):
    return request("POST", url, **kwargs)


def put(url: str, **kwargs: Any):
    return request("PUT", url, **kwargs)


class PcHttpSession:
    """Instance-owned Chrome 146 transport and CookieJar for PC API calls."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory or _transport().Session
        self._session = self._new_session()
        self._source_cookie_fingerprint: str | None = None
        self._closed = False
        self._lock = threading.RLock()

    def _new_session(self):
        return self._session_factory(
            impersonate=PC_IMPERSONATE,
            default_headers=False,
        )

    @staticmethod
    def _cookie_fingerprint(cookies: dict[str, str]) -> str:
        normalized = "\n".join(f"{key}={cookies[key]}" for key in sorted(cookies))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _replace_session(self) -> None:
        old_session = self._session
        self._session = self._new_session()
        old_session.close()

    def sync_cookies(self, cookies_str: str) -> None:
        if not cookies_str or not str(cookies_str).strip():
            raise ValueError("cookies must be a non-empty cookie string")
        cookies = {
            key: value
            for key, value in trans_cookies(str(cookies_str)).items()
            if key
        }
        if not cookies:
            raise ValueError("cookies must contain at least one named value")
        fingerprint = self._cookie_fingerprint(cookies)
        with self._lock:
            self._ensure_open()
            if self._source_cookie_fingerprint == fingerprint:
                return
            if self._source_cookie_fingerprint is not None:
                self._replace_session()
                logger.info("Reset PC HTTP session after caller Cookie change")
            for key, value in cookies.items():
                self._session.cookies.set(
                    key,
                    value,
                    domain=_COOKIE_DOMAIN,
                    path="/",
                    secure=True,
                )
            self._source_cookie_fingerprint = fingerprint
            logger.debug(
                "Imported caller Cookies into PC session cookie_count={}",
                len(cookies),
            )

    def prepare_cookies(self, cookies_str: str) -> str:
        self.sync_cookies(cookies_str)
        return self.export_cookies()

    def export_cookies(self) -> str:
        with self._lock:
            self._ensure_open()
            cookies = self._session.cookies.get_dict()
            return "; ".join(f"{key}={value}" for key, value in cookies.items())

    def request(self, method: str, url: str, **kwargs: Any):
        request_kwargs = dict(kwargs)
        request_kwargs.pop("cookies", None)
        request_kwargs.setdefault("default_headers", False)
        request_kwargs.setdefault("accept_encoding", PC_ACCEPT_ENCODING)
        started_at = perf_counter()
        path = urlsplit(url).path
        with self._lock:
            self._ensure_open()
            try:
                response = self._session.request(method, url, **request_kwargs)
            except Exception as exc:
                logger.warning(
                    "PC HTTP request failed method={} path={} profile={} proxy={} error_type={}",
                    method.upper(),
                    path,
                    PC_IMPERSONATE,
                    bool(request_kwargs.get("proxies")),
                    type(exc).__name__,
                )
                raise
            logger.debug(
                "PC HTTP request method={} path={} status={} elapsed_ms={:.1f} profile={} proxy={}",
                method.upper(),
                path,
                getattr(response, "status_code", None),
                (perf_counter() - started_at) * 1000,
                PC_IMPERSONATE,
                bool(request_kwargs.get("proxies")),
            )
        return response

    def get(self, url: str, **kwargs: Any):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any):
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any):
        return self.request("PUT", url, **kwargs)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._session.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("PC HTTP session is closed")

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
