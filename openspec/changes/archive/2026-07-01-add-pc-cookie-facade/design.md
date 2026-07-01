## Context

Spider_XHS currently exposes PC crawling through `apis.xhs_pc_apis.XHS_Apis`, whose methods require callers to pass `cookies_str` and `proxies` on each call and to handle `(success, msg, data)` tuples. The script-level `spider.Data_Spider` adds some useful normalization for notes, but it is coupled to media downloads and Excel output. RedNote2TG needs a dependency-friendly API that can call PC crawling features with cookie authentication only.

## Goals / Non-Goals

**Goals:**

- Provide a stable `XhsPcClient` entry point for PC crawling.
- Accept cookies once in the client constructor and inject them into calls.
- Preserve raw `XHS_Apis` access for debugging and less-common calls.
- Provide stable convenience methods for search, homefeed, user notes, note detail, comments, messages, and watermark helpers.
- Package Spider_XHS so it can be used as an editable path or git dependency.

**Non-Goals:**

- Implement QR-code, phone, or creator login flows.
- Wrap creator publishing, PuGongYing, or QianFan APIs.
- Convert the existing synchronous requests implementation to async.
- Move all existing modules under a new namespace in this change.
- Download media or save Excel from the facade.

## Decisions

1. Add a new `spider_xhs` package as the public facade.

   Rationale: It avoids changing existing modules and keeps current script behavior intact. A deeper namespace migration can happen later if needed.

   Alternative considered: Rename `apis` and `xhs_utils` into `spider_xhs.*`. That would be cleaner long term, but it is a larger refactor with higher break risk.

2. Use constructor-level cookie authentication.

   Rationale: RedNote2TG will manage cookie configuration externally. The facade only needs to inject `cookies_str` into existing PC calls.

   Alternative considered: Add login helpers now. This would expand scope and pull in interactive flows that TG does not need yet.

3. Keep `client.raw` as direct access to `XHS_Apis`.

   Rationale: Spider_XHS tracks a volatile upstream service. Raw access gives maintainers a debugging escape hatch without expanding stable facade methods for every edge case.

   Trade-off: Raw methods still require manual cookies/proxies. Stable facade methods are the preferred external API.

4. Normalize only note detail results in this change.

   Rationale: `handle_note_info` already defines the data shape RedNote2TG needs for Telegram upload. Search/homefeed/user-list methods can optionally fetch detail when callers request it.

   Alternative considered: Normalize all raw item types. That would require more field contracts and real endpoint fixtures.

5. Add packaging metadata while retaining top-level legacy packages.

   Rationale: This allows immediate dependency use with minimal code movement. `static/*.js` must be included because signing helpers load these files at runtime.

## Risks / Trade-offs

- Upstream response fields change -> Stable methods raise `XhsApiError`; raw access remains available for diagnosis.
- Bulk `with_detail=True` can make many network calls -> Default remains lightweight and callers opt into detail fetches.
- Packaging still exposes legacy top-level `apis` and `xhs_utils` packages -> Accept short term to avoid a broad import rewrite.
- No real network tests -> Add unit tests with mocked raw API responses and keep live endpoint verification manual.
