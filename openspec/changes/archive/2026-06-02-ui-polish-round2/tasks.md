## 1. Label Localization

- [x] 1.1 `InsightCard.tsx` — thêm `TIER_LABEL` map, đổi tier badge sang Vietnamese
- [x] 1.2 `InsightDetail.tsx` — thêm `TIER_LABEL` map, đổi tier badge sang Vietnamese
- [x] 1.3 `InsightDetail.tsx` — thêm `ADOPTION_LABEL` map, đổi adoption badge sang Vietnamese
- [x] 1.4 `InsightDetail.tsx` — fix practical indicators: `Migr`→`Hướng dẫn chuyển đổi`, `Sec`→`Bản vá bảo mật`, `Bench`→`Benchmark`, `Code`→`Mã nguồn`
- [x] 1.5 `Breadcrumb.tsx` — đồng bộ `TIER_LABELS` map: `Tactical`→`Hành động ngay`, `Informational`→`Tham khảo`

## 2. Detail Page: Bỏ Score Bars + Khôi Phục Split View

- [x] 2.1 `InsightDetail.tsx` — xóa biến `trustPct`, `actionPct`, `confidencePct`
- [x] 2.2 `InsightDetail.tsx` — xóa toàn bộ sidebar `<aside>` block (score bars + vai trò + nguồn gốc)
- [x] 2.3 `InsightDetail.tsx` — đổi `detailArticleLayout` → `detailSplitView` (50/50)
- [x] 2.4 `InsightDetail.tsx` — cột phải: render OriginalArticlePanel mở sẵn (collapsed=false)
- [x] 2.5 `InsightDetail.tsx` — di chuyển source link vào header (detailSourceTime)
- [x] 2.6 Responsive ≤1024px — đã có trong detail.module.css `.detailSplitView` media query

## 3. Card Thumbnail Placeholder

- [x] 3.1 `InsightCard.tsx` — luôn render thumbnail area, hiện placeholder gradient + 📰 icon khi null/error
- [x] 3.2 `card.module.css` — thêm `.cardThumbnailPlaceholder` class (gradient + dashed border + centered icon)

## 4. Dark Mode & Warm-tone Fix

- [x] 4.1 `dashboard.module.css` — thêm `html[data-theme="dark"]` overrides cho `.kpiDanger`, `.kpiSuccess`, `.kpiInfo` (subtle alpha 0.06)
- [x] 4.2 `dashboard.module.css` — fix warm-tone: `rgba(49, 35, 18, ...)` → `rgba(79, 70, 229, ...)`
- [x] 4.3 `dashboard.module.css` — fix chip active colors: `rgba(184, 77, 30, ...)` → indigo `rgba(79, 70, 229, ...)`

## 5. Final Verification

- [x] 5.1 `npm run build` — 0 TypeScript errors, 157 modules, 48KB CSS
- [ ] 5.2 Visual verify: tất cả badges tiếng Việt
- [ ] 5.3 Visual verify: detail page 50/50, không có score bars
- [ ] 5.4 Visual verify: dark mode — KPI mềm, chips cool
