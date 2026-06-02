## ADDED Requirements

### Requirement: Intelligence tier filter dropdown

Dashboard MUST có dropdown filter cho `intelligence_tier` trên trang InsightList.

#### Scenario: Render dropdown
- **WHEN** trang InsightList load
- **THEN** hiển thị dropdown "Phân tầng" với 5 options: "Tất cả", "Chiến thuật (Tactical)", "Vận hành (Operational)", "Chiến lược (Strategic)", "Thông tin (Informational)"
- **THEN** default = "Tất cả"

#### Scenario: Chọn filter tier
- **WHEN** user chọn "Chiến thuật (Tactical)"
- **THEN** API call thêm param `intelligence_tier=tactical`
- **THEN** danh sách insight chỉ hiển thị tier tactical

### Requirement: Sort by actionability score

Dashboard MUST hỗ trợ sort insights theo `actionability_score`.

#### Scenario: Sort option mới
- **WHEN** user mở sort dropdown trên InsightList
- **THEN** có thêm option "Mức độ hành động" bên cạnh "Mới nhất"
- **THEN** chọn "Mức độ hành động" → API call `sort_by=actionability_score&sort_order=desc`

### Requirement: Intelligence tier badge trên InsightCard

InsightCard MUST hiển thị badge cho `intelligence_tier`.

#### Scenario: Render tier badge
- **WHEN** insight có `intelligence_tier = "tactical"`
- **THEN** InsightCard hiển thị badge "Chiến thuật" với màu đỏ
- **THEN** tier "operational" → badge cam, "strategic" → badge tím, "informational" → badge xám

#### Scenario: Insight không có tier (null)
- **WHEN** insight cũ có `intelligence_tier = null`
- **THEN** không hiển thị badge tier

### Requirement: So What, Adoption Ring trên InsightDetail

InsightDetail MUST hiển thị `so_what` và `adoption_ring` khi có data.

#### Scenario: Render so_what
- **WHEN** insight có `so_what` không null
- **THEN** InsightDetail hiển thị section "Ảnh hưởng" với nội dung `so_what`

#### Scenario: Render adoption_ring
- **WHEN** insight có `adoption_ring = "Trial"`
- **THEN** InsightDetail hiển thị badge "Thử nghiệm" (Trial)
- **THEN** Adopt → "Nên dùng ngay", Trial → "Thử nghiệm", Assess → "Đánh giá thêm", Hold → "Chờ đợi"

#### Scenario: Render practical_indicators
- **WHEN** insight có `practical_indicators` không null
- **THEN** InsightDetail hiển thị icon row: ✅ cho true flags, ❌ cho false
- **THEN** Labels: has_code_example → "Có code mẫu", has_benchmark → "Có benchmark", has_api_change → "Thay đổi API", has_migration_guide → "Hướng dẫn migration", has_security_patch → "Bản vá bảo mật"
