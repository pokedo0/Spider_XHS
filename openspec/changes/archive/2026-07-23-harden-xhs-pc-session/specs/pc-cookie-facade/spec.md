## ADDED Requirements

### Requirement: PC client lifecycle
The system SHALL allow callers to close an owned PC transport explicitly or through a context manager.

#### Scenario: Context manager exit
- **WHEN** a caller leaves an `XhsPcClient` context manager
- **THEN** the client closes the raw API and HTTP session that it owns

#### Scenario: Injected raw API
- **WHEN** an `XhsPcClient` was constructed with an injected raw API
- **THEN** closing the facade does not close that externally owned object

### Requirement: Refreshed Cookie export
The system SHALL expose the current request-ready CookieJar snapshot as a Cookie string.

#### Scenario: Export after Set-Cookie
- **WHEN** the server has updated the client CookieJar
- **THEN** `export_cookies()` returns a Cookie string containing the current values while the original `cookies` attribute remains compatible
