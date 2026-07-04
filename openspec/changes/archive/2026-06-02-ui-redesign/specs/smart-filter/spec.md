## ADDED Requirements

### Requirement: Active Filter Chips
Bộ lọc đang active hiển thị dưới dạng chip (tag) trên toolbar, mỗi chip có nút "x" để xóa riêng lẻ.

#### Scenario: Chip hiển thị khi filter active
- **WHEN** người dùng chọn filter `urgency` = "critical"
- **THEN** một chip "Cấp thiết: Nghiêm trọng" xuất hiện trên toolbar với icon "x" bên phải

#### Scenario: Xóa chip individual
- **WHEN** người dùng click "x" trên chip "Cấp thiết: Nghiêm trọng"
- **THEN** chip biến mất, filter `urgency` = "critical" bị gỡ, danh sách insight cập nhật ngay

#### Scenario: Nhiều chip hiển thị đồng thời
- **WHEN** người dùng chọn 3 filter khác nhau
- **THEN** cả 3 chip hiển thị inline trên toolbar, wrap sang dòng mới nếu không đủ chỗ

### Requirement: Result Count
Số lượng kết quả sau khi lọc hiển thị rõ ràng trên toolbar.

#### Scenario: Đếm kết quả sau filter
- **WHEN** người dùng áp dụng filter và có 42 insight khớp
- **THEN** hiển thị text "42 kết quả" trên toolbar, cập nhật realtime khi filter thay đổi

#### Scenario: Không có kết quả
- **WHEN** filter trả về 0 insight
- **THEN** hiển thị "0 kết quả" và vùng content hiển thị empty state message "Không tìm thấy insight phù hợp"

### Requirement: Client-side Search
Ô search lọc client-side trên các field `title`, `summary_short`, và `signal`. Search áp dụng debounce 300ms.

#### Scenario: Search theo title
- **WHEN** người dùng gõ "GPT" vào ô search
- **THEN** sau 300ms debounce, chỉ hiển thị insight có "GPT" trong title, summary_short, hoặc signal (case-insensitive)

#### Scenario: Search kết hợp với filter
- **WHEN** người dùng đã chọn filter `urgency` = "critical" và gõ "AI" vào search
- **THEN** chỉ hiển thị insight vừa khớp urgency=critical VÀ chứa "AI" trong text fields

#### Scenario: Xóa search text
- **WHEN** người dùng xóa hết text trong ô search (hoặc click clear icon)
- **THEN** bỏ filter search, danh sách trở về state chỉ có filter (nếu có) active

### Requirement: Filter Drawer Slide-in
Filter panel trượt vào từ bên phải (drawer) thay vì dropdown. Drawer có overlay backdrop.

#### Scenario: Mở filter drawer
- **WHEN** người dùng click nút "Bộ lọc" trên toolbar
- **THEN** drawer trượt vào từ phải với animation 0.3s, backdrop overlay xuất hiện phía sau

#### Scenario: Đóng filter drawer
- **WHEN** người dùng click nút đóng (X) trên drawer hoặc click backdrop
- **THEN** drawer trượt ra về phía phải và biến mất, backdrop ẩn

#### Scenario: Drawer không block scroll trên desktop
- **WHEN** filter drawer đang mở trên viewport ≥ 1024px
- **THEN** main content bên trái vẫn visible (drawer chiếm tối đa 360px width)

### Requirement: Grouped Filters with Accordion
Trong drawer, filter được nhóm theo category với accordion collapse/expand: Phân tầng, Cấp thiết, Xu hướng, Việt Nam, Vai trò, Nguồn.

#### Scenario: Accordion expand/collapse
- **WHEN** người dùng click header "Phân tầng"
- **THEN** section Phân tầng expand hiển thị các option (Tactical, Operational, Strategic, Informational); click lại thì collapse

#### Scenario: Nhiều section mở đồng thời
- **WHEN** người dùng expand "Phân tầng" rồi expand "Cấp thiết"
- **THEN** cả 2 section đều mở đồng thời, cho phép xem và chọn nhiều nhóm filter cùng lúc

#### Scenario: Count hiển thị trên mỗi group header
- **WHEN** người dùng đã chọn 2 filter trong nhóm "Phân tầng"
- **THEN** header "Phân tầng" hiển thị badge count "(2)" bên cạnh title

### Requirement: Preset Buttons
Toolbar có preset buttons cho 3 bộ lọc thường dùng, luôn hiển thị (không trong drawer).

#### Scenario: Preset "🔥 Khẩn cấp" kích hoạt
- **WHEN** người dùng click preset "🔥 Khẩn cấp"
- **THEN** filter set urgency = ["critical", "high"], preset button có visual active state, chip tương ứng xuất hiện

#### Scenario: Preset "🇻🇳 Việt Nam" kích hoạt
- **WHEN** người dùng click preset "🇻🇳 Việt Nam"
- **THEN** filter set vietnam_relevance = "high", preset button active, chip xuất hiện

#### Scenario: Preset "📈 Đang nổi" kích hoạt
- **WHEN** người dùng click preset "📈 Đang nổi"
- **THEN** filter set momentum = "rising", preset button active, chip xuất hiện

### Requirement: Xóa Tất Cả Filter
Nút "Xóa tất cả" xóa toàn bộ filter đang active, bao gồm cả search text và preset.

#### Scenario: Xóa tất cả filter
- **WHEN** người dùng có 3 filter active + search text và click "Xóa tất cả"
- **THEN** tất cả chip biến mất, search text trống, preset buttons deactive, danh sách insight reset về state không filter

#### Scenario: Nút ẩn khi không có filter
- **WHEN** không có filter nào active (bao gồm search text rỗng)
- **THEN** nút "Xóa tất cả" bị ẩn hoặc disabled
