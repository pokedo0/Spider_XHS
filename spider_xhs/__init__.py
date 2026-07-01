"""Public facade for Spider_XHS."""

from spider_xhs.errors import XhsApiError
from spider_xhs.pc import XhsPcClient

__all__ = ["XhsApiError", "XhsPcClient"]
