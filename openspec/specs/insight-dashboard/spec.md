## Purpose

Insight Dashboard UI cho phép team đa vai trò (Engineering, Data/AI, Product, Legal, Executive...) xem insights đã phân tích, lọc theo urgency/momentum/role và đọc khuyến nghị hành động cụ thể cho vai trò của mình.
## Requirements
### Requirement: Trang danh sách Insights

React page MUST hiển thị danh sách insight dưới dạng cards, fetch từ backend API.

#### Scenario: Hiển thị danh sách insight
- **WHEN** user truy cập trang chủ (`/`)
- **THEN** hiển thị danh sách insight cards, mỗi card gồm: title, summary_short, topics (tags), impact_label (badge màu), event_type, thời gian (relative: "2 giờ trước")

#### Scenario: Loading state
- **WHEN** đang fetch dữ liệu từ API
- **THEN** hiển thị skeleton loading (không blank screen)

#### Scenario: Empty state
- **WHEN** API trả về 0 insights
- **THEN** hiển thị message "Chưa có insight nào. Chạy ingestion để bắt đầu thu thập dữ liệu."

#### Scenario: Error state
- **WHEN** API call thất bại (network error, 500)
- **THEN** hiển thị error message với nút "Thử lại"

### Requirement: Trang chi tiết Insight

Khi click vào 1 insight card, app MUST navigate tới trang chi tiết.

#### Scenario: Hiển thị chi tiết
- **WHEN** user click vào 1 insight card
- **THEN** navigate tới `/insights/:id` và hiển thị: title, summary_medium (full), topics, event_type, nature, trust_score, impact_label, source_url (link clickable mở tab mới), created_at

#### Scenario: Link về nguồn gốc
- **WHEN** user click vào source_url trên trang detail
- **THEN** mở link gốc (GitHub Changelog post) trong tab mới

#### Scenario: Insight không tồn tại
- **WHEN** user truy cập `/insights/:id` với id không hợp lệ
- **THEN** hiển thị "Insight không tìm thấy" với link quay về trang chủ

### Requirement: Impact label màu sắc

Impact label MUST có visual indicator rõ ràng bằng màu.

#### Scenario: Màu theo impact level
- **WHEN** insight card hoặc detail hiển thị impact_label
- **THEN** badge dùng màu: Critical → đỏ, High → cam, Medium → vàng, Low → xanh lá, Watch → xám

### Requirement: Responsive và hiệu năng

Dashboard MUST responsive và load nhanh.

#### Scenario: Mobile responsive
- **WHEN** user mở trang trên màn hình < 768px
- **THEN** cards chuyển sang layout 1 cột, text vẫn đọc được, không bị cắt

#### Scenario: Pagination UI
- **WHEN** có nhiều hơn 20 insights
- **THEN** hiển thị pagination controls (Previous/Next) ở cuối danh sách

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

### Requirement: Card không hiện badge trùng

InsightCard MUST chỉ render 1 trong 2 (UrgencyBadge HOẶC ImpactBadge), không cả 2 cùng lúc.

#### Scenario: Insight có urgency
- **WHEN** insight có `urgency` ≠ null
- **THEN** card render `<UrgencyBadge>`
- **THEN** card KHÔNG render `<ImpactBadge>` (dù `impact_label` ≠ null)

#### Scenario: Insight cũ chưa có urgency
- **WHEN** insight có `urgency = null` và `impact_label` ≠ null
- **THEN** card render `<ImpactBadge>` như cũ
- **THEN** không có UrgencyBadge

#### Scenario: Cả 2 đều null
- **WHEN** insight có `urgency = null` và `impact_label = null`
- **THEN** card không render badge nào ở slot này

### Requirement: MomentumIndicator chỉ render `rising`

MomentumIndicator MUST hide cho `momentum ∈ {new, mature, null}`. Chỉ render khi `momentum = "rising"`.

#### Scenario: Momentum = rising
- **WHEN** insight có `momentum = "rising"`
- **THEN** render pill `🔥 Đang nổi lên`

#### Scenario: Momentum = new
- **WHEN** insight có `momentum = "new"`
- **THEN** component return `null` (không render)

#### Scenario: Momentum = mature hoặc null
- **WHEN** insight có `momentum = "mature"` hoặc `null`
- **THEN** component return `null`

### Requirement: Sort "Ảnh hưởng cao nhất" dùng urgency
Sort option "Ảnh hưởng cao nhất" MUST gửi `sort_by=urgency` đến API (thay vì `sort_by=impact_label`) để đồng nhất với `UrgencyBadge` hiển thị trên InsightCard.

#### Scenario: Sort theo urgency
- **WHEN** người dùng chọn "Ảnh hưởng cao nhất" trong SortDropdown
- **THEN** danh sách insights được sắp xếp theo thứ tự: critical → high → medium → low, ưu tiên published_at DESC trong cùng mức urgency

#### Scenario: Badge đồng nhất với sort
- **WHEN** sort "Ảnh hưởng cao nhất" được active
- **THEN** badge hiển thị trên card (UrgencyBadge) phản ánh đúng thứ tự sắp xếp — insights có badge "KHẨN CẤP" xuất hiện trước "CAO" trước "TRUNG BÌNH"

### Requirement: Role filter chip không hiển thị count
Role filter chips MUST không hiển thị số đếm insight per role (count SHALL là undefined).

#### Scenario: Role chips không có số
- **WHEN** người dùng xem tab "Vai trò"
- **THEN** mỗi role chip chỉ hiển thị tên vai trò, không có số đếm kèm theo

#### Scenario: Role chips vẫn toggle được
- **WHEN** người dùng click vào role chip
- **THEN** chip được chọn/bỏ chọn bình thường và filter hoạt động đúng

### Requirement: RoleBadge hỗ trợ 5 role mới

`RoleBadge` MUST có color mapping cho 5 role mới (DevOps, Infrastructure, Security, BA/QA, Designer/UX), tránh trùng màu với 8 role hiện có.

#### Scenario: Render role mới
- **WHEN** insight có `affected_roles` chứa `"Security"`
- **THEN** RoleBadge render với màu red-orange (#dc2626 hoặc tương tự)

#### Scenario: Render role chưa có mapping
- **WHEN** role không thuộc 13 entries (lỗi data hoặc role mới)
- **THEN** RoleBadge fallback màu gray default, không crash

