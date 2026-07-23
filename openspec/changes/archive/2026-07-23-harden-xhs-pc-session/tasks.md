## 1. Browser Profile and Signing

- [x] 1.1 Define the Windows Chrome 146 PC profile and minimum curl_cffi version
- [x] 1.2 Merge complete API headers with xhshow and legacy signing output
- [x] 1.3 Align page-navigation helpers with the Chrome 146 profile

## 2. Stateful Transport and Errors

- [x] 2.1 Implement the instance-owned PC HTTP session and CookieJar synchronization
- [x] 2.2 Route raw PC API requests through the session using effective Cookies
- [x] 2.3 Centralize defensive response parsing and secret-safe request logging

## 3. Public Facade

- [x] 3.1 Add raw API and facade lifecycle methods plus refreshed Cookie export
- [x] 3.2 Enrich XhsApiError while preserving existing constructor compatibility

## 4. Verification

- [x] 4.1 Add deterministic tests for profiles, signing merges, Cookie updates, response failures, and lifecycle
- [x] 4.2 Run the repository verification commands and validate the OpenSpec change
