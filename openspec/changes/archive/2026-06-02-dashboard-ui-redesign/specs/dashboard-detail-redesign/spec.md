## ADDED Requirements

### Requirement: Hero Image Header
Trang chi tiết insight phải có hero image header full-width với gradient overlay, title, và metadata badges.

#### Scenario: Hero image render khi insight có primary_image
- **WHEN** trang InsightDetail load insight có primary_image
- **THEN** hiển thị hero image full-width (max-height 360px, min-height 240px), gradient overlay tối từ dưới lên (black 0.6 → transparent), title + source + time overlay trên ảnh

#### Scenario: Hero fallback khi không có image
- **WHEN** insight KHÔNG có primary_image
- **THEN** hiển thị gradient header với topic-themed color scheme thay cho image, vẫn giữ layout title + badges

### Requirement: Article-Style Reading Layout
AI Summary phải hiển thị ở dạng article-style (main content + sidebar) thay vì split 50/50 hiện tại.

#### Scenario: Desktop layout 70/30
- **WHEN** viewport ≥ 1024px
- **THEN** AI Summary chiếm 70% width (trái), Sidebar chiếm 30% width (phải, sticky khi scroll)

#### Scenario: Sidebar chứa metadata và actions
- **WHEN** sidebar render
- **THEN** phải chứa (theo thứ tự): Score cards (trust, actionability, confidence), Affected roles (badges), Topics (tags), Practical indicators, References links

#### Scenario: Mobile stacks vertically
- **WHEN** viewport ≤ 768px
- **THEN** sidebar hiển thị dưới main content, không sticky, full-width

### Requirement: Collapsible Original Content
Bài viết gốc phải hiển thị dạng collapsible section thay vì cột riêng.

#### Scenario: Bài gốc mặc định collapsed
- **WHEN** trang detail load
- **THEN** section "📰 Xem bài viết gốc" hiển thị ở dạng collapsed: chỉ thấy header bar + icon expand

#### Scenario: Click expand hiển thị full content
- **WHEN** user click header "📰 Xem bài viết gốc"
- **THEN** section expand với slide-down animation (300ms), hiển thị: featured image, title, source info, và full original text content

### Requirement: Summary Sections Visual Upgrade
Các section trong AI summary ("Điều cần biết", "Tại sao quan tâm", "Phân tích thêm", "Rủi ro") phải có visual distinction rõ ràng.

#### Scenario: Mỗi section có icon và color coding
- **WHEN** AI summary render
- **THEN** mỗi section phải có: icon header (📋 💡 🔎 👥 ⚠️), left border color (mỗi section khác nhau), background tint nhẹ, border-radius 16px

#### Scenario: "Tại sao bạn nên quan tâm" nổi bật nhất
- **WHEN** section "Tại sao bạn nên quan tâm" render
- **THEN** phải có background accent gradient, font-size lớn hơn body 1 step, và icon 💡 lớn — đây là CTA chính
