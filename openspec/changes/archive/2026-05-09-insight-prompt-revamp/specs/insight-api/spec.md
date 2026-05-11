## ADDED Requirements

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
