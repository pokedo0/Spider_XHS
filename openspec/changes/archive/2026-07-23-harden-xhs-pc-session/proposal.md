## Why

PC requests currently combine an unpinned curl impersonation profile with hard-coded Chrome 121/122 headers, and the default xhshow signer path can omit the normal browser headers entirely. Requests also discard response cookie updates and can hide useful Xiaohongshu error details behind `KeyError("msg")`, making risk-control failures harder to avoid and diagnose.

## What Changes

- Fix the PC transport profile to Windows Chrome 146 across TLS/HTTP2 and HTTP headers.
- Ensure both xhshow and legacy signing paths produce complete browser headers.
- Reuse a per-client HTTP session so connections and response cookies survive across requests.
- Add explicit client/session lifecycle and current-cookie export APIs.
- Parse error responses defensively and expose structured error context without logging secrets.

## Capabilities

### New Capabilities
- `pc-request-session`: Defines the stable Chrome profile, stateful cookie/session behavior, lifecycle, and safe error observability for PC requests.

### Modified Capabilities
- `pc-cookie-facade`: Adds lifecycle and refreshed-cookie export behavior to the public `XhsPcClient` facade while preserving existing methods.

## Impact

Affected areas include `xhs_utils` HTTP/signing helpers, `apis.xhs_pc_apis.XHS_Apis`, the public `spider_xhs.XhsPcClient` facade, tests, and the minimum `curl_cffi` dependency.
