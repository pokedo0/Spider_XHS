## 1. Package Setup

- [x] 1.1 Add the public `spider_xhs` package entry point.
- [x] 1.2 Add packaging metadata for editable/git dependency usage and include static signing assets.

## 2. PC Facade

- [x] 2.1 Implement `XhsPcClient` with constructor-level cookies and proxies.
- [x] 2.2 Add stable methods for note detail, batch note detail, search, homefeed, user notes, comments, notifications, and watermark helpers.
- [x] 2.3 Preserve raw `XHS_Apis` access through `client.raw`.

## 3. Tests

- [x] 3.1 Add unit tests with mocked PC API calls for cookie injection, note normalization, lightweight search, detailed search, comments, and error behavior.
- [x] 3.2 Add import/package-data verification for the new public package.

## 4. Verification

- [x] 4.1 Run focused tests.
- [x] 4.2 Run OpenSpec validation for the change.
