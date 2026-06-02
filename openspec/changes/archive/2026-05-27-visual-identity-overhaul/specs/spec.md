## ADDED Requirements

### Requirement: Cool Neutral Color Palette
Toàn bộ dashboard phải sử dụng hệ màu cool-neutral thay vì warm earth.

#### Scenario: Background và surface colors
WHEN người dùng truy cập dashboard
THEN background chính hiển thị màu cool off-white (#f8f9fb)
AND cards hiển thị nền true white (#ffffff) với shadow rõ ràng
AND accent chính là indigo (#4f46e5) cho links, buttons, active states

#### Scenario: Semantic colors
WHEN hiển thị badges urgency/impact
THEN sử dụng amber (#f59e0b) cho warning, red (#ef4444) cho danger, emerald (#10b981) cho success
AND warmth chỉ xuất hiện ở semantic elements, không ở background/surface

---

### Requirement: Typography System Mới
Dashboard phải sử dụng font display Plus Jakarta Sans và body font Geist/Inter.

#### Scenario: Font rendering
WHEN trang load hoàn tất
THEN titles và headers hiển thị bằng Plus Jakarta Sans (weight 600-800)
AND body text hiển thị bằng Geist hoặc Inter fallback (weight 400-600)
AND fonts load với `display=swap` để tránh FOIT

---

### Requirement: Card Visual Tối Giản
Cards trên list page phải hiển thị tối đa 4 elements thay vì 7+.

#### Scenario: Card content hierarchy
WHEN hiển thị insight card trên danh sách
THEN card hiển thị: source+time, title, 1-line summary, max 2 badges
AND KHÔNG hiển thị bullet points trên card (chỉ trên detail page)
AND KHÔNG hiển thị original English title trên card

#### Scenario: Card depth
WHEN card ở trạng thái bình thường
THEN card có shadow-2 (visible depth)
WHEN user hover card
THEN card có shadow-3 + translateY(-6px) + border accent color

---

### Requirement: Metadata Ribbon Compact
Detail page ribbon phải hiển thị badges inline trên 1 dòng, bỏ section labels.

#### Scenario: Ribbon layout
WHEN hiển thị metadata ribbon trên detail page
THEN tất cả badges (tier, urgency, momentum, roles, topics) xếp ngang liên tục
AND KHÔNG có section titles ("PHÂN LOẠI", "ĐỐI TƯỢNG", "CHỦ ĐỀ")
AND ribbon chiếm tối đa 1-2 dòng
