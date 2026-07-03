from __future__ import annotations

from typing import Any


DEFAULT_IMPERSONATE = "chrome"


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
