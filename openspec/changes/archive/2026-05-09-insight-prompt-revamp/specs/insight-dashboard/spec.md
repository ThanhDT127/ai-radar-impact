## ADDED Requirements

### Requirement: InsightCard hiển thị urgency badge và signal

Card MUST hiển thị `urgency` badge nổi bật + `signal` (nếu có) thay cho summary để truyền tải nhanh "tại sao quan trọng".

#### Scenario: Card có urgency badge
- **WHEN** insight có `urgency` ≠ null
- **THEN** card render badge với màu phù hợp:
  - `critical` → đỏ
  - `high` → cam
  - `medium` → vàng
  - `low` → xám

#### Scenario: Card hiển thị signal khi có
- **WHEN** insight có `signal` ≠ null
- **THEN** card hiển thị `signal` ở vị trí ưu tiên (trên summary_short)

#### Scenario: Fallback cho insight cũ
- **WHEN** insight không có `signal` (insight cũ chưa regenerate)
- **THEN** card hiển thị `summary_short` như cũ

#### Scenario: Card hiển thị momentum indicator
- **WHEN** insight có `momentum = "rising"`
- **THEN** card render icon/text "Đang nổi lên" (hoặc tương tự)
- **WHEN** `momentum = "new"`
- **THEN** card render icon "Mới"

### Requirement: InsightDetail hiển thị recommendations theo role

Trang detail MUST có section "Khuyến nghị cho team" hiển thị `recommendations` phân nhóm theo role.

#### Scenario: Detail có recommendations
- **WHEN** insight có `recommendations` non-empty
- **THEN** detail page render section "Khuyến nghị" với heading + group theo role
- **THEN** mỗi group hiển thị `action_type` (badge: watch/read/test/PoC/roadmap) + `note`

#### Scenario: Detail có why_it_matters
- **WHEN** insight có `why_it_matters` ≠ null
- **THEN** detail page render section "Tại sao quan trọng" prominent (sau title, trước summary)

#### Scenario: Detail có risks
- **WHEN** insight có `risks` non-empty
- **THEN** detail page render section "Rủi ro cần cân nhắc" với bullet list

#### Scenario: Detail không có fields mới
- **WHEN** insight cũ không có 7 fields mới
- **THEN** detail page hide các sections "Khuyến nghị", "Tại sao quan trọng", "Rủi ro" — không render placeholder/N/A
