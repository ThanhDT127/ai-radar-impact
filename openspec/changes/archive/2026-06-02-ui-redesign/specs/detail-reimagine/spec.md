## ADDED Requirements

### Requirement: Layout 70/30
Detail page chuyển từ layout 50/50 (split view) sang 70/30 — main content chiếm 70% width bên trái, sidebar chiếm 30% bên phải.

#### Scenario: Layout render đúng tỷ lệ trên desktop
- **WHEN** detail page render trên viewport ≥ 1024px
- **THEN** main content chiếm khoảng 70% width, sidebar chiếm khoảng 30%, gap giữa 2 cột là 24px

#### Scenario: Layout stack trên mobile
- **WHEN** detail page render trên viewport < 768px
- **THEN** sidebar collapse xuống dưới main content, cả 2 chiếm full width, sidebar nằm sau content

#### Scenario: Layout trên tablet
- **WHEN** detail page render trên viewport 768px–1023px
- **THEN** tỷ lệ chuyển sang 60/40 hoặc stack tùy không gian, content vẫn readable

### Requirement: Original Article Collapsible
Bài viết gốc (original article) chuyển từ panel cạnh bên sang section collapse bên dưới main content. Mặc định collapsed.

#### Scenario: Bài viết gốc mặc định collapsed
- **WHEN** detail page load
- **THEN** section "Bài viết gốc" hiển thị header với chevron icon, nội dung ẩn (collapsed)

#### Scenario: Expand bài viết gốc
- **WHEN** người dùng click header "Bài viết gốc"
- **THEN** section expand với animation slide-down, hiển thị toàn bộ nội dung bài viết gốc, chevron xoay 180°

#### Scenario: Collapse lại bài viết gốc
- **WHEN** người dùng click header "Bài viết gốc" khi đang expand
- **THEN** section collapse lại với animation, ẩn nội dung, chevron trở về hướng ban đầu

### Requirement: Sticky Sidebar
Sidebar phải sticky khi scroll, chứa: trust score bar, actionability score bar, confidence bar, affected roles, topics.

#### Scenario: Sidebar sticky khi scroll
- **WHEN** người dùng scroll main content xuống dưới
- **THEN** sidebar giữ vị trí fixed (sticky) với `top: 80px` (dưới header), không scroll cùng content

#### Scenario: Sidebar hiển thị đầy đủ scores
- **WHEN** insight có `trust_score` = 0.75, `actionability_score` = 0.6, `confidence` = 0.85
- **THEN** sidebar hiển thị 3 progress bar với label + giá trị: "Độ tin cậy: 75%", "Khả năng hành động: 60%", "Độ tự tin AI: 85%"

#### Scenario: Sidebar hiển thị roles và topics
- **WHEN** insight có `affected_roles` = ["CTO", "Developer"] và `topics` = ["LLM", "Automation"]
- **THEN** sidebar hiển thị danh sách roles và topics dưới dạng badge/tag chips

#### Scenario: Score = 0 hoặc null
- **WHEN** một score field là 0 hoặc null
- **THEN** progress bar hiển thị 0% hoặc "N/A", không crash hoặc hiển thị NaN

### Requirement: Breadcrumb Navigation
Breadcrumb hiển thị đường dẫn: Trang chủ > [Tier] > [Title truncated 50 chars].

#### Scenario: Breadcrumb render đúng
- **WHEN** detail page của insight tier "Strategic" title "Xu hướng AI tạo sinh trong ngành sản xuất toàn cầu năm 2026 và tác động"
- **THEN** breadcrumb hiển thị: "Trang chủ > Strategic > Xu hướng AI tạo sinh trong ngành sản xuất..."

#### Scenario: Breadcrumb link hoạt động
- **WHEN** người dùng click "Trang chủ" trên breadcrumb
- **THEN** navigate về trang danh sách insight (/) mà không reload trang

#### Scenario: Tier link trên breadcrumb
- **WHEN** người dùng click tier name trên breadcrumb
- **THEN** navigate về trang danh sách với filter tier tương ứng đã active

### Requirement: So What Section nổi bật
"So What" section đặt ngay dưới title, trước metadata ribbon, với visual prominence (background highlight, larger font).

#### Scenario: So What hiển thị nổi bật
- **WHEN** insight có `so_what` không rỗng
- **THEN** "So What" section render với background highlight (`--color-surface-raised`), font-size lớn hơn body text, padding 16px, border-radius 8px

#### Scenario: So What rỗng
- **WHEN** insight có `so_what` là null hoặc rỗng
- **THEN** section "So What" không render, layout dịch lên tự nhiên không có gap thừa

### Requirement: Compact Metadata Ribbon
Metadata ribbon (source, published date, tier badge, urgency badge) vẫn hiển thị nhưng compact hơn.

#### Scenario: Metadata ribbon compact
- **WHEN** detail page render
- **THEN** metadata ribbon hiển thị 1 dòng: source name + published date + tier badge + urgency badge, font-size `--text-sm`, gap 12px

### Requirement: Back Link Enlarged
Link quay lại danh sách phải lớn hơn và dễ nhìn hơn.

#### Scenario: Back link dễ thấy
- **WHEN** detail page render
- **THEN** back link "← Quay lại danh sách" có font-size `--text-base`, color `--color-primary`, padding đủ lớn (8px 0), hover underline
