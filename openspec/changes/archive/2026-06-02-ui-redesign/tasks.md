## 1. CSS Architecture Cleanup & Foundation

- [x] 1.1 Tạo `src/api/client.ts` — shared Axios instance, update imports trong `insights.ts`, `sources.ts`, `stats.ts`
- [x] 1.2 Thêm `primary_image` vào `InsightListItem` type trong `src/types/insight.ts`, xóa cast `(insight as any).primary_image` trong `InsightCard.tsx`
- [x] 1.3 Tạo `src/styles/pagination.module.css` — migrate pagination classes từ `insights.module.css`, update import trong `Pagination.tsx`
- [x] 1.4 Tạo `src/styles/badges.module.css` — migrate badge/pill/role/tier/momentum/topic/event/indicator classes, update imports trong `UrgencyBadge.tsx`, `RoleBadge.tsx`, `MomentumIndicator.tsx`
- [x] 1.5 Tạo `src/styles/card.module.css` — migrate card classes, update import trong `InsightCard.tsx`
- [x] 1.6 Tạo `src/styles/list.module.css` — migrate list page classes, update import trong `InsightList.tsx`
- [x] 1.7 Tạo `src/styles/detail.module.css` — migrate detail page classes, update import trong `InsightDetail.tsx` + `OriginalArticlePanel.tsx`
- [x] 1.8 Xóa dead CSS từ v1-v3 (không còn import insights.module.css ⇒ auto dropped khỏi bundle)
- [x] 1.9 Fix warm-tone remnants: đã fix trong pagination.module.css và detail.module.css
- [x] 1.10 Xóa `src/components/ImpactBadge.tsx` (dead code — không import ở đâu)
- [x] 1.11 Verify build pass — ✅ 47KB CSS (giảm 43% so với 83KB), 0 TypeScript errors

## 2. Card System Redesign

- [x] 2.1 Thêm tier color CSS variables vào `global.css`: `--tier-tactical`, `--tier-operational`, `--tier-strategic`, `--tier-informational`
- [x] 2.2 Implement left border 4px color-coded by `intelligence_tier` trong `card.module.css`
- [x] 2.3 Implement urgency strip 3px ở top card cho `critical` (red, pulse animation) và `high` (orange, static)
- [x] 2.4 Cập nhật `InsightCard.tsx`: tính `tierColor` và `isUrgent`, render urgency strip element, set inline style cho card border
- [x] 2.5 Tăng prominence cho `so_what` snippet
- [x] 2.6 Compact badge row: di chuyển urgency badge + tier badge + momentum inline
- [x] 2.7 Thêm 🇻🇳 flag indicator cho cards có `vietnam_relevance === 'high'`
- [x] 2.8 Card hover glow: thay đổi `box-shadow` khi hover theo tier color (alpha 0.15)
- [ ] 2.9 Visual verify: lướt card grid, kiểm tra Tactical (red border) vs Informational (gray) phân biệt rõ ràng

## 3. Dark Mode

- [x] 3.1 Tạo `src/contexts/ThemeContext.tsx`
- [x] 3.2 Tạo `src/components/ThemeToggle.tsx`
- [x] 3.3 Thêm `html[data-theme="dark"]` block vào `global.css`
- [x] 3.4 Thêm `transition: background-color 0.3s, color 0.3s, border-color 0.3s` vào body
- [x] 3.5 Wrap `App.tsx` trong `<ThemeProvider>`, thêm `<ThemeToggle>` vào `Layout.tsx` header
- [ ] 3.6 Test dark mode trên: KPI cards, insight cards, filter chips, badges, pagination, detail page sections, sidebar
- [ ] 3.7 Verify contrast accessibility: badge text trên dark surface, muted text readability, gradient backgrounds

## 4. Smart Filter Bar

- [x] 4.1 Tạo filter drawer component trong `InsightList.tsx`
- [x] 4.2 CSS cho drawer: `transform: translateX(100%)` → `translateX(0)`, backdrop, max-width `min(420px, 85vw)`
- [x] 4.3 Di chuyển 6 filter rows vào drawer, giữ preset buttons trên toolbar
- [x] 4.4 Thêm search bar trong drawer — client-side filter trên `title` + `summary_short` + `so_what`
- [x] 4.5 Thêm active filter chips row dưới toolbar
- [x] 4.6 Thêm result count display
- [x] 4.7 "Xóa tất cả" reset cả search query
- [ ] 4.8 Test filter flow

## 5. Detail Page Reimagine

- [x] 5.1 Tạo `src/components/Breadcrumb.tsx`
- [x] 5.2 Thay đổi `InsightDetail.tsx` layout: từ `1fr 1fr` (50/50) sang `7fr 3fr` (70/30)
- [x] 5.3 Tái sử dụng `OriginalArticlePanel.tsx` — import + render dưới main content
- [x] 5.4 Xóa inline original article code, thay bằng `<OriginalArticlePanel>` collapsible
- [x] 5.5 Tạo sticky sidebar 30%: trust/actionability/confidence score bars, affected roles, source link
- [x] 5.6 Compact metadata ribbon
- [x] 5.7 Thêm Breadcrumb component vào đầu detail page
- [x] 5.8 Responsive: ≤1024px collapse về single column (CSS đã có)
- [ ] 5.9 Verify: navigate từ list → detail → back

## 6. Micro-interactions & Polish

- [x] 6.1 Card entrance stagger: tạo `useCardEntrance` hook dùng `IntersectionObserver`, CSS `@keyframes fadeSlideUp`, `animation-delay` theo index × 60ms
- [x] 6.2 KPI number counting: `requestAnimationFrame` loop trong `KPISummary.tsx`, easing `easeOutCubic`, duration 800ms
- [x] 6.3 Filter chip bounce: CSS `@keyframes chipBounce` — appended to dashboard.module.css
- [x] 6.4 Tạo `src/components/ScrollToTop.tsx`
- [x] 6.5 Thêm `ScrollToTop` vào `Layout.tsx`
- [x] 6.6 Skeleton shimmer upgrade: cool indigo palette trong card.module.css
- [x] 6.7 Thêm `@media (prefers-reduced-motion: reduce)` — disable card entrance, urgency pulse, chip bounce animations
- [x] 6.8 Tạo `src/components/ErrorBoundary.tsx`
- [x] 6.9 Wrap routes trong `App.tsx` bằng `<ErrorBoundary>`

## 7. Final Verification

- [x] 7.1 Build production: `npm run build` — ✅ 0 errors, 157 modules, CSS 47.23KB (giảm 43%)
- [x] 7.2 Xóa `insights.module.css` khỏi bundle — zero imports remaining, auto-dropped by Vite
- [ ] 7.3 Visual test list page
- [ ] 7.4 Visual test detail page
- [ ] 7.5 Dark mode test
- [ ] 7.6 Responsive test
- [ ] 7.7 Performance check
