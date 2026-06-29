## ADDED Requirements

### Requirement: Card Entrance Animation
Card xuất hiện với hiệu ứng staggered fade-in khi scroll vào viewport, sử dụng IntersectionObserver.

#### Scenario: Card fade-in khi scroll vào viewport
- **WHEN** card chưa visible và người dùng scroll cho đến khi card xuất hiện trong viewport
- **THEN** card fade-in từ `opacity: 0` + `translateY(20px)` đến `opacity: 1` + `translateY(0)` với duration 0.4s ease-out

#### Scenario: Staggered delay giữa các card
- **WHEN** nhiều card cùng xuất hiện trong viewport đồng thời
- **THEN** mỗi card có delay tăng dần (card thứ n delay n × 80ms), tạo hiệu ứng cascade từ trên xuống dưới

#### Scenario: Animation chỉ chạy lần đầu
- **WHEN** card đã xuất hiện (đã animated) và người dùng scroll đi rồi scroll lại
- **THEN** card giữ nguyên trạng thái visible, không replay animation

#### Scenario: Tôn trọng prefers-reduced-motion
- **WHEN** OS setting `prefers-reduced-motion: reduce` được bật
- **THEN** tất cả animation bị disable, card hiển thị ngay lập tức không có fade/slide

### Requirement: KPI Count-up Animation
Giá trị KPI (số) chạy animated count-up từ 0 đến giá trị thực khi load lần đầu.

#### Scenario: Count-up animation khi page load
- **WHEN** KPI panel render lần đầu với value = 156
- **THEN** số hiển thị chạy từ 0 lên 156 trong khoảng 1.5s, easing ease-out (nhanh lúc đầu, chậm dần)

#### Scenario: Count-up với số thập phân
- **WHEN** KPI value là 85.5 (percentage)
- **THEN** count-up hiển thị đúng 1 decimal place trong suốt animation, kết thúc ở "85.5"

#### Scenario: Count-up không chạy khi reduced motion
- **WHEN** `prefers-reduced-motion: reduce` active
- **THEN** giá trị KPI hiển thị ngay giá trị cuối cùng, không animation

### Requirement: Filter Chip Bounce
Filter chip có subtle scale bounce khi toggle active/inactive.

#### Scenario: Bounce khi activate chip
- **WHEN** người dùng click để activate một filter chip
- **THEN** chip scale lên 1.05 rồi về 1.0 trong 0.15s, tạo cảm giác "click" responsive

#### Scenario: Bounce khi deactivate chip
- **WHEN** người dùng click để deactivate một filter chip (click "x")
- **THEN** chip scale xuống 0.95 rồi fade-out trước khi biến mất

### Requirement: Scroll-to-top Button
Floating button "Scroll to top" xuất hiện khi người dùng scroll xuống quá 400px.

#### Scenario: Button xuất hiện khi scroll down
- **WHEN** `window.scrollY` > 400px
- **THEN** floating button xuất hiện ở góc dưới phải (bottom: 24px, right: 24px) với fade-in animation

#### Scenario: Button ẩn khi gần đầu trang
- **WHEN** `window.scrollY` ≤ 400px
- **THEN** button fade-out và ẩn, không chiếm layout space

#### Scenario: Click scroll to top
- **WHEN** người dùng click button scroll-to-top
- **THEN** trang scroll mượt (smooth behavior) về đầu trang (`scrollTo({ top: 0, behavior: 'smooth' })`)

### Requirement: Card Hover Glow
Card có subtle glow border matching tier color khi hover, bổ sung hiệu ứng translateY đã có.

#### Scenario: Glow border khi hover
- **WHEN** người dùng hover lên card có `intelligence_tier` = "Strategic"
- **THEN** card hiển thị `box-shadow` glow với màu purple (tier color) nhẹ nhàng, kết hợp với translateY(-2px) đã có

#### Scenario: Glow transition mượt
- **WHEN** mouse enter và leave card
- **THEN** glow xuất hiện và biến mất với transition 0.2s ease, không giật

### Requirement: Page Scroll Progress Bar
Detail page có thanh progress mỏng ở top viewport thể hiện % đã scroll.

#### Scenario: Progress bar theo scroll position
- **WHEN** người dùng scroll detail page
- **THEN** thanh gradient mỏng (3px) ở top viewport mở rộng width từ 0% đến 100% tương ứng scroll progress

#### Scenario: Progress bar chỉ trên detail page
- **WHEN** người dùng ở trang danh sách (InsightList)
- **THEN** không hiển thị progress bar

### Requirement: Loading Skeleton cải tiến
Loading skeleton dùng gradient colors matching cool indigo palette thay vì gray mặc định.

#### Scenario: Skeleton dùng cool palette
- **WHEN** data đang loading và skeleton hiển thị
- **THEN** skeleton shimmer gradient dùng tông `--color-surface` → `--color-surface-raised` → `--color-surface`, matching indigo cool palette

#### Scenario: Skeleton dark mode compatible
- **WHEN** skeleton hiển thị trong dark mode
- **THEN** gradient colors tự động adapt theo dark theme tokens, không bị chói hoặc quá tối
