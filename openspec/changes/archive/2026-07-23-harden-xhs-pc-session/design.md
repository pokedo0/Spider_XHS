## Context

PC API calls currently use module-level `curl_cffi.requests` functions, parse the caller's Cookie string for every request, and disable curl's default browser headers whenever signed headers are present. The default xhshow path returns signing headers only, while legacy headers identify older Chrome versions than the TLS profile. RedNote2TG needs one client to retain connection and Cookie state for its process lifetime.

## Goals / Non-Goals

**Goals:**
- Produce one deterministic Windows Chrome 146 profile for every PC API request.
- Preserve response Cookie updates in an instance-owned HTTP session and use the effective Cookie state for later signatures.
- Keep raw API return tuples and existing facade methods compatible.
- Preserve actionable error status/code/message without exposing credentials.

**Non-Goals:**
- No login, publishing, PuGongYing, or QianFan facade expansion.
- No automatic retry, delay, proxy rotation, or fabricated Cookie values.
- No guarantee against account-, IP-, or behavior-based risk control.

## Decisions

- `get_request_headers_template()` remains the authoritative API header factory. `generate_request_params()` merges signer output over that template so xhshow and legacy produce the same complete request shape.
- `get_common_headers()` remains the page-navigation profile used by the no-watermark HTML helper.
- The transport uses `chrome146`, `default_headers=False`, and explicit Windows Chrome 146 headers. This avoids curl's macOS navigation defaults contaminating API requests.
- `XHS_Apis` owns a `PcHttpSession` by default. It imports a normalized caller Cookie set once, keeps server updates in the CookieJar, and recreates the underlying session when the caller supplies a different normalized Cookie set.
- Cookie signing uses the current CookieJar snapshot. Request calls do not also pass the original `cookies=` mapping.
- Response parsing is centralized but preserves `(success, msg, data)`. The facade enriches `XhsApiError` with optional code and response data.
- `XhsPcClient` closes only raw APIs it creates; injected raw APIs remain caller-owned.

## Risks / Trade-offs

- [Chrome 146 may later become old] → Keep the profile explicit and covered by tests so upgrades are deliberate.
- [Flattening CookieJar entries can collapse duplicate names] → Scope imported Cookies to `.xiaohongshu.com` and document export as a request-ready snapshot.
- [Session changes touch many raw call sites] → Route all request/sign/parse behavior through small helpers and retain method signatures.
- [Logs can expose secrets] → Log only method, path, status, code, bounded message, timing, profile, and proxy presence.
