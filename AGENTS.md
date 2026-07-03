# Spider_XHS Agent Notes

## Project Shape

Spider_XHS keeps the original low-level modules (`apis`, `xhs_utils`, `spider`) and adds a public facade package under `spider_xhs`.

Current public dependency entry point:

```python
from spider_xhs import XhsPcClient, XhsApiError

client = XhsPcClient(cookies=cookies_str, proxies=proxies)
```

The facade is cookie-only. Do not add QR-code login, phone login, creator publishing, PuGongYing, or QianFan behavior to `XhsPcClient` unless the public contract is deliberately expanded.

## Recent Facade Change

The `spider_xhs` package wraps PC crawling APIs from `apis.xhs_pc_apis.XHS_Apis`:

- `XhsPcClient` in `spider_xhs/pc.py`
- `XhsApiError` in `spider_xhs/errors.py`
- package exports in `spider_xhs/__init__.py`
- packaging metadata in `pyproject.toml`
- static asset packaging via `static/__init__.py` and `static = ["*.js"]`
- facade tests in `tests/test_pc_facade.py`

The facade exposes stable methods for:

- homefeed channels and notes
- user info and self info
- user posted, liked, and collected notes
- note detail and batch note detail
- search keywords, notes, and users
- note comments
- unread messages, mentions, likes/collects, and new connections
- no-watermark media helpers

It also preserves the raw low-level API through `client.raw`.

## Facade Compatibility Rules

Treat `spider_xhs.XhsPcClient` as an external public API.

When changing low-level PC crawling code, check whether facade behavior must be updated:

- If an `XHS_Apis` method signature changes, update `XhsPcClient` call sites and tests.
- If Xiaohongshu response fields change, update facade normalization and mocked fixtures.
- If note URL construction changes, update `note_url_from_item`.
- If `handle_note_info` changes output fields, verify RedNote2TG-facing note data still contains media URLs and author/title/description fields.
- If adding a new stable facade method, add tests and document whether it returns raw data or normalized data.
- Keep lightweight list methods lightweight by default. Only fetch per-note detail when `with_detail=True`.
- Keep `client.raw` available for diagnostics and unsupported edge cases.

Avoid breaking or renaming existing facade methods without a migration note.

## Packaging Rules

Spider_XHS is intended to be installable as an editable path or git dependency:

```bash
pip install -e .
```

Signing helpers load JavaScript from `static/*.js` at runtime, so package-data handling is required. Before changing package layout, verify that these assets still resolve through `xhs_utils.xhs_util._STATIC_DIR`.

The project still exposes legacy top-level packages (`apis`, `xhs_utils`, `spider`). Do not do a broad namespace migration without a separate plan, because it will touch many imports.

## Verification

Run focused checks after facade changes:

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q spider_xhs tests
python -m pip install -e . --dry-run --no-deps
```

For RedNote2TG/OpenSpec work, the archived change is:

```text
D:\Program\java_project\RedNote2TG\openspec\changes\archive\2026-07-01-add-pc-cookie-facade
```

The synced spec is:

```text
D:\Program\java_project\RedNote2TG\openspec\specs\pc-cookie-facade\spec.md
```

## Testing and Scratch Scripts

Whenever you are asked to write scratch scripts, integration tests, or perform any code-based testing and experimentation, always place these files under the `tests/` directory (e.g., `tests/scratch_extract.py` or `tests/test_something.py`). Do not clutter the project root with temporary or test scripts.

## Git Notes

Do not auto-commit. This repository may contain local IDE and CodeGraph files. Avoid reverting user changes or generated indexes unless explicitly asked.
