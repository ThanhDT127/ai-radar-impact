## MODIFIED Requirements

### Requirement: Insight API response chứa fields mới

API response cho insight MUST trả thêm 5 fields mới trong JSON object.

#### Scenario: GET /api/v1/insights/{id} trả fields mới
- **WHEN** client GET chi tiết 1 insight
- **THEN** JSON response chứa thêm: `actionability_score` (float|null), `intelligence_tier` (string|null), `so_what` (string|null), `adoption_ring` (string|null), `practical_indicators` (object|null)

#### Scenario: GET /api/v1/insights trả fields mới trong list
- **WHEN** client GET danh sách insights
- **THEN** mỗi item trong `items[]` chứa `actionability_score`, `intelligence_tier`, `so_what`, `adoption_ring`
- **THEN** `practical_indicators` KHÔNG trả trong list view (chỉ detail view) để giảm payload

## ADDED Requirements

### Requirement: Filter theo intelligence_tier

API MUST hỗ trợ filter insights theo `intelligence_tier`.

#### Scenario: Filter tactical
- **WHEN** client GET `/api/v1/insights?intelligence_tier=tactical`
- **THEN** response chỉ chứa insights có `intelligence_tier = "tactical"`

#### Scenario: Filter nhiều tiers
- **WHEN** client GET `/api/v1/insights?intelligence_tier=tactical,operational`
- **THEN** response chứa insights có tier là "tactical" HOẶC "operational"

### Requirement: Sort theo actionability_score

API MUST hỗ trợ sort insights theo `actionability_score`.

#### Scenario: Sort descending
- **WHEN** client GET `/api/v1/insights?sort_by=actionability_score&sort_order=desc`
- **THEN** insights sắp xếp theo `actionability_score` giảm dần
- **THEN** insights có `actionability_score = NULL` xếp cuối

#### Scenario: Sort mặc định (không đổi)
- **WHEN** client GET `/api/v1/insights` không có sort_by param
- **THEN** sắp xếp theo `created_at` DESC (giữ nguyên behavior cũ)
