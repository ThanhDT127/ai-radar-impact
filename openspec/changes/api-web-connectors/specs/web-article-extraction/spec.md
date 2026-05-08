## ADDED Requirements

### Requirement: Extract article content từ URL
WebArticleConnector dùng trafilatura để extract nội dung chính từ web pages, loại bỏ ads/nav/sidebar.

#### Scenario: Extract thành công
- **WHEN** `WebArticleConnector.extract(url)` được gọi với URL hợp lệ
- **THEN** trả về plain text nội dung bài viết chính, không chứa ads/nav/sidebar

#### Scenario: Extract metadata
- **WHEN** trafilatura extract thành công
- **THEN** trả kèm metadata: `author`, `date`, `title` (nếu có)

#### Scenario: URL không truy cập được
- **WHEN** URL timeout hoặc trả HTTP error
- **THEN** trả None, log warning

#### Scenario: Content rỗng
- **WHEN** trafilatura không extract được nội dung (SPA site, paywall, etc.)
- **THEN** trả None, log warning

### Requirement: Content length filter
Bài viết quá ngắn không đủ chất lượng cho AI analysis.

#### Scenario: Min content length
- **WHEN** normalized_content < `min_content_length` (default 200 chars)
- **THEN** skip bài đó, không lưu vào `raw_documents`
