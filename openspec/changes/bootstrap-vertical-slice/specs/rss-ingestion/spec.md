## ADDED Requirements

### Requirement: RSS feed fetching

Hệ thống phải fetch được RSS feed từ URL đã cấu hình, parse XML thành danh sách entries, và lưu mỗi entry thành 1 raw document trong database.

#### Scenario: Fetch RSS feed thành công
- **WHEN** chạy ingestion cho source có `ingest_method=rss` và `feed_url=https://github.blog/changelog/feed/`
- **THEN** hệ thống fetch RSS XML, parse ra danh sách entries, mỗi entry tạo 1 record trong `raw_documents`

#### Scenario: Feed không truy cập được
- **WHEN** RSS feed URL trả về HTTP error hoặc timeout (>30s)
- **THEN** ghi log error với source_id, URL, HTTP status, không tạo raw document nào, không crash pipeline

#### Scenario: Feed XML không hợp lệ
- **WHEN** RSS feed trả về nội dung không phải XML hợp lệ
- **THEN** ghi log warning, skip source này, tiếp tục pipeline cho source khác (nếu có)

### Requirement: HTML normalization

Raw content từ RSS thường chứa HTML tags, entities, inline styles. Normalizer phải clean thành plain text có cấu trúc.

#### Scenario: Clean HTML thành plain text
- **WHEN** raw document có `raw_content` chứa HTML tags (`<p>`, `<a>`, `<code>`, `<ul>`)
- **THEN** normalizer trả về plain text giữ nguyên nội dung ngữ nghĩa, bỏ HTML tags, giữ line breaks hợp lý

#### Scenario: Extract metadata từ RSS entry
- **WHEN** parse 1 RSS entry
- **THEN** extract được: `title`, `published_date` (ISO 8601), `source_url` (link gốc), `author` (nếu có)

### Requirement: Deduplication bằng fingerprint

Không lưu trùng document đã xử lý trước đó. Dùng content fingerprint (hash) để detect duplicate.

#### Scenario: Document mới (chưa có trong DB)
- **WHEN** fingerprint (SHA-256 của `source_url + title`) chưa tồn tại trong `raw_documents`
- **THEN** tạo record mới với status `pending`

#### Scenario: Document trùng (đã ingest trước)
- **WHEN** fingerprint đã tồn tại trong `raw_documents`
- **THEN** skip document này, ghi log debug "duplicate skipped", không tạo record mới

### Requirement: CLI trigger

Ingestion được trigger thủ công bằng CLI command (chưa cần scheduler tự động).

#### Scenario: Trigger ingestion cho tất cả active sources
- **WHEN** chạy `python -m backend.scripts.run_ingestion`
- **THEN** fetch + normalize + dedup cho tất cả sources có `status=active`, log kết quả (số new, số skipped, số errors)

#### Scenario: Trigger ingestion cho 1 source cụ thể
- **WHEN** chạy `python -m backend.scripts.run_ingestion --source-id <uuid>`
- **THEN** chỉ xử lý source có id đó
