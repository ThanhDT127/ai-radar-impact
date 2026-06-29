## Why

Dashboard hiện tại (M6) hoạt động ổn định nhưng giao diện đang có nhiều vấn đề ảnh hưởng đến trải nghiệm đọc và ra quyết định:

- **Card grid thiếu visual hierarchy** — insight "Critical" trông y hệt "Low" khi lướt nhanh, buộc user phải đọc badge nhỏ ở footer
- **CSS codebase phình to** — `insights.module.css` 2,272 dòng, chứa ~400 dòng CSS chết từ v1-v3, warm-toned remnants xung đột cool indigo palette
- **Filter UX phức tạp** — 6 hàng filter bung ra cùng lúc, không có result count, không có removable chips
- **Thiếu dark mode** — analyst đọc nhiều tin cần dark mode; CSS variables đã chuẩn bị nhưng chưa implement
- **Detail page layout 50/50** quá hẹp cho AI analysis column, metadata ribbon quá nhiều badge gây visual noise
- **Dead components** — ImpactBadge.tsx, OriginalArticlePanel.tsx không được sử dụng; 3 Axios instances riêng biệt
- **Thiếu micro-interactions** — dashboard cảm giác "static", không có entrance animation, number counting, hay scroll feedback

Phase áp dụng: **Phase 1** — cải tiến frontend M6, không thay đổi backend API.

## What Changes

Redesign toàn bộ frontend dashboard với 6 sáng kiến chính, giữ nguyên stack (React 19 + Vite + CSS Modules + TanStack Query) và backend API. Tập trung vào visual polish, UX flow, và code cleanup.

## Capabilities

### New Capabilities
- `card-redesign`: Redesign insight card system — left border theo tier color, urgency strip, so_what as primary snippet, compact badge row
- `dark-mode`: Theme system với dark mode toggle, localStorage persistence, smooth transition
- `smart-filter`: Progressive disclosure filter bar — inline search, active filter chips, result count, slide-in drawer
- `detail-reimagine`: Detail page layout 70/30, collapsible original article, sticky sidebar, breadcrumb navigation
- `micro-interactions`: Card entrance stagger, KPI number counting, filter chip feedback, scroll progress, back-to-top
- `css-cleanup`: Tách insights.module.css, xóa CSS chết, normalize badge system, fix warm-tone remnants

### Modified Capabilities
- `insight-list`: Card grid + filter UX thay đổi cấu trúc, thêm search, result count
- `insight-detail`: Layout restructure 70/30, metadata ribbon compact, original article collapsible

## Impact

**Frontend files thay đổi:**
- `src/components/InsightCard.tsx` — restructure card layout
- `src/components/KPISummary.tsx` — animated counting, click-to-filter
- `src/components/Layout.tsx` — dark mode toggle, enhanced header
- `src/pages/InsightList.tsx` — filter bar redesign, search integration
- `src/pages/InsightDetail.tsx` — 70/30 layout, collapsible sections
- `src/styles/*.module.css` — tách file, cleanup, dark mode variables
- Xóa: `ImpactBadge.tsx`, `OriginalArticlePanel.tsx` (dead code)
- Mới: `src/components/ThemeToggle.tsx`, `src/components/ScrollToTop.tsx`, `src/components/Breadcrumb.tsx`

**Không thay đổi:** Backend API, database schema, AI pipeline, routes registration.

## Non-goals

- Không thêm backend API mới (search full-text, stats history, related insights sẽ làm change riêng)
- Không thay đổi data model hay thêm cột mới
- Không implement admin UI hay user management
- Không dùng animation library (chỉ CSS transitions + requestAnimationFrame)
- Không redesign mobile-first — cải thiện responsive nhưng desktop vẫn là primary
