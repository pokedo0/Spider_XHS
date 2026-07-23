## ADDED Requirements

### Requirement: Consistent PC browser profile
The system SHALL send PC requests with a fixed Chrome 146 TLS/HTTP profile and matching Windows Chrome 146 HTTP headers.

#### Scenario: Signed API request
- **WHEN** either the xhshow or legacy signer generates headers for a PC API request
- **THEN** the final request contains the complete Chrome 146 API header set plus the generated signing headers

#### Scenario: Page navigation request
- **WHEN** the no-watermark video helper fetches a Xiaohongshu page
- **THEN** the request uses the Chrome 146 page-navigation header set and the same Chrome 146 impersonation target

### Requirement: Stateful PC Cookie session
The system SHALL retain applicable response Cookies and connection state within each PC API client instance.

#### Scenario: Server updates Cookies
- **WHEN** a PC response supplies `Set-Cookie` values
- **THEN** subsequent requests and signing operations use the updated CookieJar without reapplying the original Cookie string

#### Scenario: Caller replaces credentials
- **WHEN** the caller supplies a different normalized Cookie set to the same raw API object
- **THEN** the system replaces the old HTTP session before using the new credentials

### Requirement: Safe PC response diagnostics
The system SHALL preserve useful HTTP and Xiaohongshu error context without requiring every endpoint to contain a `msg` field.

#### Scenario: Error response omits msg
- **WHEN** an API response contains a code or alternative message field but no `msg`
- **THEN** the returned failure message contains the available status, code, and message instead of raising `KeyError`

#### Scenario: Response is not JSON
- **WHEN** a PC endpoint returns a non-JSON response where JSON is expected
- **THEN** the system returns a sanitized parse failure and logs no Cookie or signing values
