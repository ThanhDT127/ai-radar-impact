## 1. Design System Foundation

- [x] 1.1 Cập nhật `global.css` — thay Google Fonts (Inter + JetBrains Mono), thêm full typography scale, spacing scale, elevation system, semantic color tokens
- [x] 1.2 Tạo `layout.module.css` — chuyển toàn bộ inline styles từ Layout.tsx sang CSS Module
- [x] 1.3 Cập nhật `Layout.tsx` — remove inline styles, import CSS Module, giữ nguyên structure

## 2. Badge System Upgrade

- [x] 2.1 Cập nhật `UrgencyBadge.tsx` — thêm prefix "Cấp thiết:" cho labels, glassmorphism style, dùng design tokens
- [x] 2.2 Cập nhật `ImpactBadge.tsx` — thêm prefix "Ảnh hưởng:" cho labels, glassmorphism style, dùng design tokens
- [x] 2.3 Cập nhật `RoleBadge.tsx` — glassmorphism style, border-radius 8px thay 999px, dùng design tokens
- [x] 2.4 Cập nhật `MomentumIndicator.tsx` — thêm support cho "new" và "mature" states, glassmorphism style
- [x] 2.5 Cập nhật `TooltipContent.ts` — viết lại tất cả tooltip bằng tiếng Việt dễ hiểu, bỏ thuật ngữ kỹ thuật

## 3. KPI Summary Redesign

- [x] 3.1 Cập nhật API `stats.ts` — thêm field `trend_direction` và `previous_total` vào stats API call
- [x] 3.2 Cập nhật types `insight.ts` — thêm StatsResponse type với trend fields
- [x] 3.3 Redesign `KPISummary.tsx` — thêm trend arrows, phần trăm thay đổi, color coding theo direction, subtitle rõ nghĩa
- [x] 3.4 Cập nhật `dashboard.module.css` — KPI card styles mới, trend indicator styles

## 4. Filter System Redesign

- [x] 4.1 Cập nhật `InsightList.tsx` — filter panel → compact horizontal bar always-visible, "Lọc thêm ▾" toggle cho advanced
- [x] 4.2 Cập nhật `dashboard.module.css` — compact filter bar styles, slide-down animation cho advanced panel
- [x] 4.3 Cập nhật `SortDropdown.tsx` — style theo design system mới

## 5. Insight Card Redesign

- [x] 5.1 Thêm `primary_image` vào InsightListItem — cập nhật backend schema hoặc frontend API response type
- [x] 5.2 Redesign `InsightCard.tsx` — featured image, cleaner badge row, hover micro-interactions, gradient placeholder
- [x] 5.3 Cập nhật `insights.module.css` — card styles mới, featured hero card (2-col span), image aspect-ratio, skeleton shimmer
- [x] 5.4 Cập nhật grid layout trong `InsightList.tsx` — featured card đầu tiên 2-col span, responsive breakpoints

## 6. Insight Detail Redesign

- [x] 6.1 Redesign `InsightDetail.tsx` — hero image header, article-style layout 70/30, collapsible original content, sticky sidebar
- [x] 6.2 Cập nhật `OriginalArticlePanel.tsx` — chuyển thành collapsible section với slide animation
- [x] 6.3 Cập nhật `RecommendationsByRole.tsx` — card style theo design system mới
- [x] 6.4 Cập nhật `insights.module.css` — detail page styles mới, hero header, article layout, sidebar sticky

## 7. Polish & Responsive

- [x] 7.1 Responsive testing — đảm bảo layout đúng ở 1440px, 1024px, 768px, 375px
- [x] 7.2 Skeleton loading upgrade — shimmer animation premium cho cả featured card và standard cards
- [x] 7.3 Hover states và micro-interactions — kiểm tra tất cả interactive elements có transitions
- [x] 7.4 Remove unused components — xóa `TabBar.tsx` và `FilterChips.tsx` nếu không dùng

## 8. Visual QA via Chrome DevTools MCP

- [ ] 8.1 Screenshot InsightList — so sánh before/after, kiểm tra layout, spacing, typography
- [ ] 8.2 Screenshot InsightDetail — kiểm tra hero header, article layout, collapsible content
- [ ] 8.3 Console error check — đảm bảo không có runtime error, broken image, missing font
- [ ] 8.4 Responsive screenshots — mobile và tablet views
