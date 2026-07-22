## ADDED Requirements

### Requirement: `recommendations` mang mức ảnh hưởng theo từng vai trò
Mỗi entry trong `recommendations` MUST có thêm khoá `urgency` thuộc tập đóng
`high | medium | low`, thể hiện mức ảnh hưởng của tin **tới riêng vai trò đó** — KHÔNG phải mức ảnh
hưởng của tin nói chung (đã có ở `insights.urgency`). Prompt MUST hướng dẫn Gemini chấm tiết kiệm:
`high` chỉ dành cho tin mà người giữ vai trò đó cần đọc ngay trong ngày.

#### Scenario: Cùng một tin, mức khác nhau theo vai trò
- **WHEN** Gemini phân tích một lỗ hổng bảo mật trong thư viện hệ thống với `affected_roles = [Security, Dev]`
- **THEN** `recommendations["Security"].urgency` = `high` còn `recommendations["Dev"].urgency` có thể là `medium` hoặc `low`

#### Scenario: Tin không phải bảo mật vẫn có thể `high`
- **WHEN** Gemini phân tích một bản phát hành model lớn với `affected_roles` chứa `AI Engineer`
- **THEN** `recommendations["AI Engineer"].urgency` ĐƯỢC PHÉP là `high`, không phụ thuộc `event_type` hay `insights.urgency`

## MODIFIED Requirements

### Requirement: Validate `recommendations` post-parse

Sau khi parse Gemini output, backend MUST validate `recommendations` để loại bỏ keys hallucinate và
giá trị ngoài tập đóng, bao gồm cả khoá `urgency` mới.

#### Scenario: Drop role không trong affected_roles
- **WHEN** Gemini trả `recommendations` có key không thuộc `affected_roles`
- **THEN** backend remove key đó khỏi recommendations trước khi lưu
- **THEN** log warning về role bị drop

#### Scenario: Drop `action_type` không hợp lệ
- **WHEN** value của `recommendations[role]` có `action_type` không thuộc closed set
- **THEN** backend remove cả entry đó
- **THEN** log warning

#### Scenario: `urgency` không hợp lệ hoặc thiếu
- **WHEN** `recommendations[role]` có `urgency` không thuộc `high|medium|low`, hoặc không có khoá `urgency`
- **THEN** backend đặt `urgency = "medium"` cho entry đó và giữ nguyên phần còn lại của entry
- **THEN** log warning nêu rõ role và giá trị bị thay
