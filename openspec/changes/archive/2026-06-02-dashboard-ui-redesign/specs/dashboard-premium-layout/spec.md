## ADDED Requirements

### Requirement: KPI Cards với Trend Indicators
KPI cards phải hiển thị trend direction (lên/xuống/ngang) so với tuần trước, giúp người dùng nhanh chóng nhận biết xu hướng.

#### Scenario: KPI card hiển thị trend arrow
- **WHEN** dashboard load với data
- **THEN** mỗi KPI card phải hiển thị: giá trị chính (số lớn), trend arrow (▲ hoặc ▼ hoặc ―), phần trăm thay đổi so với tuần trước, và subtitle giải thích ý nghĩa

#### Scenario: Trend arrow có color coding
- **WHEN** KPI value tăng so với tuần trước
- **THEN** trend arrow phải màu xanh lá (success) cho positive metrics (Tổng bản tin, Cơ hội), màu đỏ (danger) cho negative metrics (Ảnh hưởng cao)

### Requirement: Featured Hero Card
Card đầu tiên (insight mới nhất hoặc có impact cao nhất) phải lớn gấp đôi chiều cao so với các card thường, chiếm 2 cột, tạo visual hierarchy.

#### Scenario: Card đầu tiên render ở hero size
- **WHEN** insight list render với ≥ 1 item
- **THEN** card đầu tiên phải chiếm 2 cột và có chiều cao gấp ~2x card thường, hiển thị thêm primary_image nếu có, và 2 dòng summary thay vì chỉ bullets

#### Scenario: Grid layout responsive
- **WHEN** viewport ≤ 768px (mobile)
- **THEN** featured card trở lại 1-column layout, vẫn lớn hơn card thường nhưng chỉ chiếm 1 cột

### Requirement: Compact Filter Bar Always-Visible
Thay vì toggle panel ẩn/hiện, filter bar phải luôn hiển thị ở dạng compact horizontal strip.

#### Scenario: Filter bar visible khi scroll
- **WHEN** user scroll xuống danh sách insights
- **THEN** filter bar vẫn visible (sticky hoặc inline) — không cần mở/đóng panel

#### Scenario: Filter bar compact mode
- **WHEN** filter bar render
- **THEN** phải hiển thị tối đa 1 dòng: Sort dropdown + Quick filters (Khẩn cấp, Việt Nam, Đang nổi) + "Lọc thêm ▾" button cho advanced filters

#### Scenario: Advanced filters mở inline
- **WHEN** user click "Lọc thêm ▾"
- **THEN** advanced filter rows slide xuống bên dưới filter bar (không phải modal/dialog), có animation 200ms

### Requirement: Insight Card Redesign
Card phải có thiết kế premium hơn: featured image, cleaner badge layout, hover micro-interactions.

#### Scenario: Card hiển thị primary image
- **WHEN** insight có primary_image URL
- **THEN** card phải hiển thị ảnh ở top (aspect-ratio 16:9, object-fit cover, border-radius top), title bên dưới

#### Scenario: Card hiển thị placeholder khi không có ảnh
- **WHEN** insight KHÔNG có primary_image
- **THEN** card hiển thị gradient background placeholder với topic icon thay cho ảnh

#### Scenario: Card hover effect premium
- **WHEN** user hover card
- **THEN** card phải: translateY(-4px), shadow tăng lên level 2, border subtle glow, image scale 1.03 — tất cả transition 200ms ease
