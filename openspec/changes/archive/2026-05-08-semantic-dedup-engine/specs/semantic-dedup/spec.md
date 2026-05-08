## ADDED Requirements

### Requirement: Phát hiện semantic duplicates
Hệ thống phải phát hiện insights về cùng một sự kiện từ nhiều nguồn khác nhau.

#### Scenario: Tìm duplicates
- **WHEN** batch ingestion tạo insights mới
- **THEN** so sánh insights mới với insights hiện có (7 ngày gần nhất) bằng TF-IDF cosine similarity
- **THEN** nhóm insights có similarity >= 0.6 thành 1 cluster

#### Scenario: Chọn Primary insight
- **WHEN** cluster được tạo
- **THEN** chọn insight từ nguồn có `trust_tier` cao nhất làm primary
- **THEN** các insight khác trong cluster có `is_primary = false`

#### Scenario: Insight độc lập
- **WHEN** insight không similar với bất kỳ insight nào
- **THEN** `cluster_id = NULL`, `is_primary = true`

### Requirement: API trả references
`GET /api/v1/insights/{id}` phải trả kèm danh sách references từ cùng cluster.

#### Scenario: Insight có cluster
- **WHEN** insight có `cluster_id` != NULL
- **THEN** response chứa `references` array với id, title, source_name, source_url của insights khác trong cluster

#### Scenario: Insight không có cluster
- **WHEN** insight có `cluster_id` = NULL
- **THEN** `references` = empty array

### Requirement: Dashboard chỉ hiện primary
`GET /api/v1/insights` mặc định chỉ trả primary insights.

#### Scenario: Default list
- **WHEN** gọi `GET /api/v1/insights` không có filter đặc biệt
- **THEN** chỉ trả insights có `is_primary = true` hoặc `cluster_id IS NULL`

### Requirement: Frontend hiển thị references
InsightDetail page hiển thị danh sách "Bài viết liên quan từ nguồn khác".

#### Scenario: Có references
- **WHEN** insight detail có `references.length > 0`
- **THEN** hiển thị section "Bài viết liên quan" với link đến từng reference
