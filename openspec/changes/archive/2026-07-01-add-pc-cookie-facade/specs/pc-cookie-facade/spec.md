## ADDED Requirements

### Requirement: Cookie-only PC client
The system SHALL provide a public PC crawling client that accepts a cookie string and optional proxies at construction time and uses them for stable facade calls.

#### Scenario: Construct client with cookie string
- **WHEN** a caller creates the PC client with `cookies="a1=value; web_session=value"` and optional proxies
- **THEN** subsequent stable facade calls use those credentials without requiring cookies to be passed again

### Requirement: Stable note detail retrieval
The system SHALL provide a stable method to fetch a note by URL and return normalized note fields suitable for downstream Telegram upload.

#### Scenario: Fetch note detail
- **WHEN** a caller requests note detail for a valid note URL
- **THEN** the client returns a dictionary containing `note_id`, `note_url`, `note_type`, `title`, `desc`, `image_list`, `video_addr`, `video_cover`, `tags`, and author metadata

### Requirement: Lightweight and detailed note collection methods
The system SHALL provide PC facade methods for search results, homefeed results, user posted notes, liked notes, and collected notes, with lightweight results by default and optional detail fetching.

#### Scenario: Search without detail
- **WHEN** a caller searches notes with `with_detail=False`
- **THEN** the client returns lightweight raw note items or URLs without making per-note detail calls

#### Scenario: Search with detail
- **WHEN** a caller searches notes with `with_detail=True`
- **THEN** the client fetches each resulting note detail and returns normalized note dictionaries

### Requirement: PC comments and notifications access
The system SHALL expose stable PC facade methods for note comments, unread messages, mentions, likes and collects, and new connections using cookie authentication.

#### Scenario: Fetch note comments
- **WHEN** a caller requests comments for a note URL
- **THEN** the client returns the raw comment list from the PC API using configured cookies and proxies

### Requirement: Watermark helper access
The system SHALL expose PC facade methods for no-watermark video and image URL helpers.

#### Scenario: Resolve no-watermark media
- **WHEN** a caller provides a note id or image URL to the corresponding helper
- **THEN** the client returns the resolved URL or raises a facade error when resolution fails

### Requirement: Raw API escape hatch
The system SHALL expose direct raw PC API access for maintainers while keeping stable facade methods as the recommended external API.

#### Scenario: Access raw API
- **WHEN** a caller accesses `client.raw`
- **THEN** the returned object is the underlying PC API object for advanced or diagnostic calls

### Requirement: Dependency packaging
The system SHALL package the facade and required runtime assets so Spider_XHS can be installed as a Python dependency.

#### Scenario: Install as dependency
- **WHEN** Spider_XHS is installed in editable or git dependency form
- **THEN** `from spider_xhs import XhsPcClient` succeeds and runtime signing assets under `static/*.js` are available to the existing signing helpers
