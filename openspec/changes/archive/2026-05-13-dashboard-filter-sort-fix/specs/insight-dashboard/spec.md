## MODIFIED Requirements

### Requirement: Sort "Ảnh hưởng cao nhất" dùng urgency
Sort option "Ảnh hưởng cao nhất" MUST gửi `sort_by=urgency` đến API (thay vì `sort_by=impact_label`) để đồng nhất với `UrgencyBadge` hiển thị trên InsightCard.

#### Scenario: Sort theo urgency
- **WHEN** người dùng chọn "Ảnh hưởng cao nhất" trong SortDropdown
- **THEN** danh sách insights được sắp xếp theo thứ tự: critical → high → medium → low, ưu tiên published_at DESC trong cùng mức urgency

#### Scenario: Badge đồng nhất với sort
- **WHEN** sort "Ảnh hưởng cao nhất" được active
- **THEN** badge hiển thị trên card (UrgencyBadge) phản ánh đúng thứ tự sắp xếp — insights có badge "KHẨN CẤP" xuất hiện trước "CAO" trước "TRUNG BÌNH"

## MODIFIED Requirements

### Requirement: Role filter chip không hiển thị count
Role filter chips MUST không hiển thị số đếm insight per role (count SHALL là undefined).

#### Scenario: Role chips không có số
- **WHEN** người dùng xem tab "Vai trò"
- **THEN** mỗi role chip chỉ hiển thị tên vai trò, không có số đếm kèm theo

#### Scenario: Role chips vẫn toggle được
- **WHEN** người dùng click vào role chip
- **THEN** chip được chọn/bỏ chọn bình thường và filter hoạt động đúng
