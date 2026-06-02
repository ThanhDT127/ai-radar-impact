## ADDED Requirements

### Requirement: Intelligence tier assignment

Hệ thống MUST gán `intelligence_tier` cho mỗi insight dựa trên rule-based logic (không dùng LLM), lưu vào cột `intelligence_tier` (String(20)) trong bảng `insights`.

#### Scenario: Tactical tier
- **WHEN** insight có `event_type` ∈ {"Breaking Change", "Cảnh báo bảo mật", "Sự cố vận hành"} AND `actionability_score >= 0.7`
- **THEN** `intelligence_tier = "tactical"`

#### Scenario: Operational tier
- **WHEN** insight có `event_type` ∈ {"Phát hành mới", "Ngừng hỗ trợ/Deprecation", "Hướng dẫn/Best Practice"} AND `actionability_score >= 0.5`
- **THEN** `intelligence_tier = "operational"`

#### Scenario: Strategic tier
- **WHEN** insight có `event_type` ∈ {"Tín hiệu xu hướng", "Thay đổi chính sách", "Cập nhật quy định"} AND `actionability_score >= 0.4`
- **THEN** `intelligence_tier = "strategic"`

#### Scenario: Informational fallback
- **WHEN** insight không khớp bất kỳ rule tactical/operational/strategic nào
- **THEN** `intelligence_tier = "informational"`

#### Scenario: Tactical override khi score thấp
- **WHEN** event_type ∈ {"Breaking Change", "Cảnh báo bảo mật"} BUT `actionability_score < 0.7`
- **THEN** `intelligence_tier = "operational"` (downgrade, không bỏ qua)

### Requirement: Intelligence tier phải được gán đồng bộ với actionability_score

Tier MUST được tính SAU khi actionability_score đã sẵn sàng, trong cùng transaction tạo insight.

#### Scenario: Tier gán cùng lúc tạo insight
- **WHEN** insight mới được tạo trong `analyze_document()`
- **THEN** cả `actionability_score` và `intelligence_tier` được set trước khi commit
