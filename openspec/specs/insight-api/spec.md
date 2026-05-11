## Purpose

Insight API expose insights đã phân tích qua HTTP cho frontend dashboard, hỗ trợ pagination, filter (role, source, urgency, momentum, vietnam_relevance) và sort.
## Requirements
### Requirement: List insights API

API MUST trả về danh sách insights có pagination, sắp xếp theo thời gian mới nhất.

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

API MUST trả về chi tiết 1 insight theo ID.

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

Tất cả API responses MUST tuân theo conventions đã định nghĩa trong project.

#### Scenario: Insight item trong list response
- **WHEN** insight item xuất hiện trong danh sách
- **THEN** chứa các fields: `id` (UUID), `title` (string), `summary_short` (string), `topics` (string[]), `event_type` (string), `nature` (string), `impact_label` (string), `source_url` (string), `created_at` (ISO 8601 UTC)

#### Scenario: Error response format
- **WHEN** bất kỳ API trả về error
- **THEN** body có format `{ error: string, detail: string, code: string }` — nhất quán toàn bộ API

### Requirement: Insight response trả thêm 7 actionable fields

`GET /api/v1/insights` và `GET /api/v1/insights/{id}` MUST trả thêm 7 fields mới trong response. Backwards compatible — clients hiện tại không break vì additive only.

#### Scenario: List insights có fields mới
- **WHEN** client gọi `GET /api/v1/insights`
- **THEN** mỗi insight trong response có thêm: `signal`, `why_it_matters`, `recommendations`, `risks`, `momentum`, `urgency`, `vietnam_relevance`
- **THEN** insights cũ chưa có data các field này trả `null` hoặc `[]` (rỗng cho `risks`/`recommendations`)

#### Scenario: Detail insight có fields mới
- **WHEN** client gọi `GET /api/v1/insights/{id}`
- **THEN** response có 7 fields mới ngoài các fields cũ và `references`

#### Scenario: Filter theo `urgency`
- **WHEN** client gọi `GET /api/v1/insights?urgency=critical,high`
- **THEN** response chỉ trả insights có `urgency` ∈ {critical, high}

#### Scenario: Filter theo `momentum`
- **WHEN** client gọi `GET /api/v1/insights?momentum=rising`
- **THEN** response chỉ trả insights có `momentum = "rising"`

#### Scenario: Filter theo `vietnam_relevance`
- **WHEN** client gọi `GET /api/v1/insights?vietnam_relevance=high`
- **THEN** response chỉ trả insights có `vietnam_relevance = "high"`

### Requirement: Sort theo urgency

Default sort MUST thay đổi để ưu tiên urgency cao trước.

#### Scenario: Default sort
- **WHEN** client gọi `GET /api/v1/insights` không truyền sort param
- **THEN** kết quả sort theo: `urgency` (critical→low) THEN `published_at DESC`

