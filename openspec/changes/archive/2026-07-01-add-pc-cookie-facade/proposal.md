## Why

RedNote2TG needs to consume Spider_XHS as a stable Python dependency for PC-side note crawling without depending on script-style entry points or login flows. Spider_XHS already has the low-level PC APIs, but external callers must currently know cookie plumbing, tuple return shapes, URL construction, and raw response details.

## What Changes

- Add a cookie-only PC facade package for Spider_XHS that wraps existing `XHS_Apis` methods.
- Provide a stable client entry point for search, homefeed, user notes, note detail, comments, messages, and watermark helpers.
- Keep raw PC API access available for debugging and unsupported edge cases.
- Add packaging metadata so Spider_XHS can be installed as a dependency.
- Do not add QR-code login, phone login, creator publishing, PuGongYing, or QianFan facades in this change.

## Capabilities

### New Capabilities

- `pc-cookie-facade`: Stable cookie-authenticated facade over Spider_XHS PC crawling APIs.

### Modified Capabilities

None.

## Impact

- Affected code: Spider_XHS packaging metadata and new `spider_xhs` facade package.
- Affected APIs: New public `XhsPcClient` facade while preserving existing `apis.xhs_pc_apis.XHS_Apis`.
- Dependencies: Python package metadata must include existing runtime requirements and `static/*.js` signing assets.
- Systems: RedNote2TG will be able to depend on Spider_XHS using editable path or git dependency.
