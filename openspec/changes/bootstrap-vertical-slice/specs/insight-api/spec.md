## ADDED Requirements

### Requirement: List insights API

API trả về danh sách insights có pagination, sắp xếp theo thời gian mới nhất.

#### Scenario: Lấy danh sách mặc định
- **WHEN** gọi `GET /api/v1/insights`
- **THEN** trả về `200` với body `{ page: 1, size: 20, total: <N>, items: [...] }`, sắp xếp `created_at DESC`

#### Scenario: Pagination
- **WHEN** gọi `GET /api/v1/insights?page=2&size=10`
- **THEN** trả về trang 2 với tối đa 10 items, `page=2`, `size=10`, `total` là tổng số insights

#### Scenario: Không có insight nào
- **WHEN** database chưa có insight
- **THEN** trả về `200` với `{ page: 1, size: 20, total: 0, items: [] }`

### Requirement: Insight detail API

API trả về chi tiết 1 insight theo ID.

#### Scenario: Lấy insight tồn tại
- **WHEN** gọi `GET /api/v1/insights/:id` với id hợp lệ
- **THEN** trả về `200` với full insight object bao gồm: id, title, summary_short, summary_medium, topics, event_type, nature, trust_score, impact_label, source_url, created_at

#### Scenario: Insight không tồn tại
- **WHEN** gọi `GET /api/v1/insights/:id` với id không có trong DB
- **THEN** trả về `404` với body `{ error: "Not Found", detail: "Insight not found", code: "INSIGHT_NOT_FOUND" }`

#### Scenario: ID không hợp lệ
- **WHEN** gọi `GET /api/v1/insights/:id` với id không phải UUID
- **THEN** trả về `422` validation error

### Requirement: Response format nhất quán

Tất cả API responses phải tuân theo conventions đã định nghĩa trong project.

#### Scenario: Insight item trong list response
- **WHEN** insight item xuất hiện trong danh sách
- **THEN** chứa các fields: `id` (UUID), `title` (string), `summary_short` (string), `topics` (string[]), `event_type` (string), `nature` (string), `impact_label` (string), `source_url` (string), `created_at` (ISO 8601 UTC)

#### Scenario: Error response format
- **WHEN** bất kỳ API trả về error
- **THEN** body có format `{ error: string, detail: string, code: string }` — nhất quán toàn bộ API
