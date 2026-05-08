## ADDED Requirements

### Requirement: Trigger ingestion qua API
Admin có thể trigger ingestion thủ công qua HTTP endpoint.

#### Scenario: Ingest all sources
- **WHEN** `POST /api/v1/admin/ingest` không có `source_id`
- **THEN** chạy ingestion cho tất cả sources active
- **THEN** trả response với summary (new, skipped, errors, insights_created)

#### Scenario: Ingest specific source
- **WHEN** `POST /api/v1/admin/ingest` có `source_id` query param
- **THEN** chạy ingestion chỉ cho source đó

### Requirement: Trigger analysis qua API
Admin có thể trigger AI analysis cho pending documents.

#### Scenario: Analyze pending
- **WHEN** `POST /api/v1/admin/analyze`
- **THEN** chạy analysis cho tất cả raw_documents có `processing_status = pending`
- **THEN** trả response với count (analyzed, failed)

### Requirement: Source management qua API

#### Scenario: List sources
- **WHEN** `GET /api/v1/admin/sources`
- **THEN** trả danh sách sources với stats: document count, insight count, last ingestion time

#### Scenario: Add source
- **WHEN** `POST /api/v1/admin/sources` với body chứa name, source_type, feed_url, trust_tier, topics
- **THEN** tạo source mới trong database

### Requirement: API Key authentication
Mọi admin endpoint phải được bảo vệ bằng API key.

#### Scenario: Valid API key
- **WHEN** request có header `Authorization: Bearer {ADMIN_API_KEY}`
- **THEN** cho phép truy cập

#### Scenario: Missing/Invalid API key
- **WHEN** request thiếu hoặc sai API key
- **THEN** trả 401 Unauthorized

### Requirement: Daily analysis rate limiting

#### Scenario: Dưới limit
- **WHEN** số documents đã analyze trong ngày < `MAX_DAILY_ANALYSIS`
- **THEN** cho phép analyze

#### Scenario: Vượt limit
- **WHEN** số documents đã analyze trong ngày >= `MAX_DAILY_ANALYSIS`
- **THEN** trả 429 Too Many Requests
