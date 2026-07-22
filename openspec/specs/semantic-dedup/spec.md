## Purpose

Semantic dedup gom các insight nói về cùng một sự kiện nhưng đến từ nhiều nguồn khác nhau thành một
cụm (`cluster_id`), chọn một đại diện (`is_primary`) để hiển thị và đính các bản còn lại làm
`references`. Nhờ đó dashboard không lặp cùng một tin nhiều lần, mà vẫn cho người đọc thấy tin đó
được bao nhiêu nguồn đưa.
## Requirements
### Requirement: Phát hiện semantic duplicates
Hệ thống MUST phát hiện insights về cùng một sự kiện từ nhiều nguồn khác nhau.

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
`GET /api/v1/insights/{id}` MUST trả kèm danh sách references từ cùng cluster.

#### Scenario: Insight có cluster
- **WHEN** insight có `cluster_id` != NULL
- **THEN** response chứa `references` array với id, title, source_name, source_url của insights khác trong cluster

#### Scenario: Insight không có cluster
- **WHEN** insight có `cluster_id` = NULL
- **THEN** `references` = empty array

### Requirement: Dashboard chỉ hiện primary
`GET /api/v1/insights` mặc định MUST chỉ trả primary insights. Ràng buộc "chỉ tính primary" áp cho **mọi**
bề mặt hướng người dùng của insight — cả danh sách lẫn **các con số đếm**. Bất kỳ endpoint nào trả về
số lượng insight cho người dùng (KPI thống kê, số insight theo nguồn) MUST đếm theo đại diện cụm
(`is_primary = true`), KHÔNG được đếm bản trùng đã bị gộp. Số hiển thị và số bản ghi người dùng bấm
vào xem được MUST khớp nhau.

#### Scenario: Default list
- **WHEN** gọi `GET /api/v1/insights` không có filter đặc biệt
- **THEN** chỉ trả insights có `is_primary = true` hoặc `cluster_id IS NULL`

#### Scenario: KPI thống kê không đếm bản trùng
- **WHEN** gọi `GET /api/v1/insights/stats` trong lúc DB có insight `published` với `is_primary = false`
- **THEN** cả `total`, `critical_high` và `opportunities` chỉ đếm insight `is_primary = true`

#### Scenario: Đếm insight theo nguồn khớp với danh sách
- **WHEN** gọi `GET /api/v1/sources` và một nguồn có N insight `published` trong đó chỉ M cái `is_primary = true` (M < N)
- **THEN** `insight_count` của nguồn đó bằng **M**, đúng bằng `total` mà `GET /api/v1/insights?source_id=<nguồn>` trả về

#### Scenario: Nguồn chỉ toàn bản trùng
- **WHEN** một nguồn có insight `published` nhưng tất cả đều `is_primary = false`
- **THEN** `insight_count` của nguồn đó bằng `0` (nguồn được xếp vào nhóm "chưa có insight", không thành chip lọc rỗng)

### Requirement: Frontend hiển thị references
InsightDetail page MUST hiển thị danh sách "Bài viết liên quan từ nguồn khác".

#### Scenario: Có references
- **WHEN** insight detail có `references.length > 0`
- **THEN** hiển thị section "Bài viết liên quan" với link đến từng reference

