# Design — ui-redesign

> Module bị ảnh hưởng: **M6 (Dashboard)**
> Phạm vi: Frontend-only — không thay đổi backend API, database, AI pipeline

---

## Context

Dashboard hiện tại (M6) phục vụ việc đọc và phân tích insight từ 15 nguồn RSS. Kiến trúc frontend gồm 2 page (`InsightList.tsx` — 382 dòng, `InsightDetail.tsx` — 307 dòng), 14 component, và 4 file CSS Module. Hệ thống design token trong `global.css` đã có sẵn palette cool indigo (`--color-accent: #4f46e5`) và spacing scale 8px, nhưng chưa có dark mode override.

### Vấn đề cần giải quyết

| # | Vấn đề | File liên quan | Mức độ |
|---|--------|---------------|--------|
| 1 | `insights.module.css` phình 2,272 dòng — trộn lẫn card, detail, pagination, badges, tooltip, skeleton, 4 phiên bản layout cũ | `src/styles/insights.module.css` | Cao |
| 2 | ~13 dòng warm-tone remnant `rgba(120,99,77,...)` xung đột palette cool indigo | `insights.module.css` L537–L814 | Trung bình |
| 3 | Card grid thiếu visual hierarchy — insight "Critical/Tactical" trông y hệt "Low/Informational" khi lướt nhanh | `InsightCard.tsx`, `.card` class | Cao |
| 4 | Filter panel bung 6 hàng cùng lúc (tier, urgency, momentum, vietnam, roles, sources), không có search bar hay result count | `InsightList.tsx` L270–L342, `dashboard.module.css` | Cao |
| 5 | Detail page layout 50/50 quá hẹp cho AI analysis column (`detailSplitView` — `grid-template-columns: 1fr 1fr`) | `InsightDetail.tsx` L182, `insights.module.css` L2117–L2122 | Trung bình |
| 6 | 3 Axios instance riêng biệt với config trùng lặp | `api/insights.ts`, `api/sources.ts`, `api/stats.ts` | Thấp |
| 7 | 2 component không được import ở bất kỳ đâu | `ImpactBadge.tsx`, `OriginalArticlePanel.tsx` | Thấp |
| 8 | Thiếu dark mode — analyst đọc nhiều cần chế độ tối | `global.css` (chưa có `[data-theme="dark"]`) | Trung bình |
| 9 | Không có micro-interaction — dashboard cảm giác static | Toàn bộ component | Thấp |

### API endpoints sử dụng (không thay đổi)

- `GET /api/v1/insights` — paginated list với filter params (role, source_id, urgency, momentum, vietnam_relevance, intelligence_tier, sort_by)
- `GET /api/v1/insights/:id` — chi tiết insight
- `GET /api/v1/insights/stats` — KPI aggregation (total, critical_high, opportunities, active_sources)
- `GET /api/v1/sources` — danh sách nguồn RSS

---

## Goals / Non-Goals

### Goals

1. **Tách `insights.module.css` thành 5 file module** — giảm cognitive load khi maintain, mỗi file < 400 dòng
2. **Card system với visual hierarchy rõ ràng** — nhìn lướt nhanh phân biệt được tier và urgency
3. **Dark mode hoàn chỉnh** — CSS variable override, toggle UI, persistence qua localStorage
4. **Smart filter bar** — progressive disclosure, removable chips, client-side search, result count
5. **Detail page 70/30 layout** — tăng không gian cho AI analysis, original article thành collapsible
6. **Micro-interactions** — entrance stagger, KPI counting, scroll-to-top, hover feedback
7. **Gom 3 Axios instance thành 1** — giảm duplication, dễ thêm interceptor sau này
8. **Xóa dead code** — `ImpactBadge.tsx`, `OriginalArticlePanel.tsx`, CSS classes không sử dụng

### Non-Goals

- **Không thêm backend API mới** — search full-text server-side, stats history, related insights sẽ là change riêng
- **Không thay đổi data model** — không thêm cột, không sửa schema
- **Không dùng animation library** (framer-motion, react-spring) — chỉ CSS transitions + `requestAnimationFrame`
- **Không thêm npm dependency** — tất cả implement bằng React 19 built-in + CSS
- **Không redesign mobile-first** — cải thiện responsive nhưng desktop vẫn là primary viewport
- **Không implement admin UI** hay user management

---

## Decisions

### D1: Chiến lược tách `insights.module.css`

**Quyết định:** Tách file mega CSS 2,272 dòng thành 5 file module chuyên biệt + giữ lại file gốc rỗng làm re-export hub tạm thời.

| File mới | Nội dung | Ước lượng dòng | Import bởi |
|----------|----------|---------------|------------|
| `card.module.css` | `.card`, `.cardContentRow`, `.cardTitle`, `.cardFooter`, `.cardThumbnail*`, `.tierBadgeInline`, `.cardSummarySnippet`, skeleton | ~280 | `InsightCard.tsx` |
| `detail.module.css` | `.detailPage`, `.detailHeaderWrap`, `.detailSplitView`, `.detailSection*`, `.detailSoWhat`, `.originalPanel*`, collapsible, sidebar, score bars | ~450 | `InsightDetail.tsx` |
| `badges.module.css` | `.badge*`, `.roleBadge`, `.tierBadge*`, `.adoptionBadge*`, `.momentumPill*`, `.topicTag`, `.eventTag`, `.indicatorIcon`, `.sourcePill` | ~250 | `UrgencyBadge.tsx`, `RoleBadge.tsx`, `MomentumIndicator.tsx`, card/detail |
| `pagination.module.css` | `.paginationShell`, `.pagination*`, `.paginationBtn`, `.paginationPage*`, `.paginationInput`, `.paginationJump*` | ~100 | `Pagination.tsx` |
| `list.module.css` | `.listPage`, `.hero`, `.eyebrow`, `.pageTitle`, `.panel`, `.cardGrid`, `.emptyState`, `.errorState`, skeleton (list-level) | ~120 | `InsightList.tsx` |

**Rationale:** Hiện tại `InsightCard.tsx` import `insights.module.css` để dùng ~15 class, nhưng phải load 2,272 dòng CSS. Tách file giúp:
- Tree-shaking CSS tốt hơn (Vite CSS code-splitting theo module)
- Mỗi component chỉ import đúng file cần thiết
- Review PR dễ hơn — thay đổi card style không diff vào detail style

**Migration path:**
1. Tạo 5 file mới, copy class tương ứng
2. Cập nhật import trong từng component/page
3. Giữ `insights.module.css` tạm thời với comment `/* DEPRECATED — migrated to card/detail/badges/pagination/list modules */`
4. Xóa `insights.module.css` ở task cuối sau khi verify không còn import nào

**CSS classes cần xóa (dead code từ v1-v3):**
- `.cardImageWrap`, `.cardImagePlaceholder`, `.cardImageIcon`, `.cardImageOverlay` — card layout cũ dùng hero image, hiện tại dùng inline thumbnail
- `.cardFeatured`, `.cardFeatured .cardImageWrap` — featured card concept đã bỏ
- `.splitView`, `.splitLeft`, `.splitRight`, `.splitRightHeader`, `.splitRightTitle` — layout v2, thay bằng `detailSplitView`
- `.originalIframeContainer`, `.originalIframe`, `.originalLoading`, `.originalSpinner`, `.originalFallback*` — iframe approach đã bỏ
- `.detailBody` — container v2 không còn sử dụng
- `.detailHero*`, `.detailHeroFallback` — hero image approach v3, hiện dùng `detailHeaderWrap`
- `.detailArticleLayout`, `.detailMainContent`, `.detailSidebar` — 70/30 layout v3 chưa bao giờ được component sử dụng

### D2: Dark mode — CSS variables + `data-theme` attribute

**Quyết định:** Dùng `data-theme="dark"` attribute trên `<html>` element kết hợp `prefers-color-scheme` media query. State quản lý bằng React context + localStorage.

**Cách hoạt động:**

```
┌─────────────────────────────────────────────────┐
│ User mở app lần đầu                             │
│  ├─ Check localStorage("theme")                 │
│  ├─ Nếu có → apply giá trị đã lưu              │
│  └─ Nếu không → check prefers-color-scheme      │
│       ├─ dark → set data-theme="dark"           │
│       └─ light → set data-theme="light"         │
│                                                  │
│ User click ThemeToggle                           │
│  ├─ Toggle data-theme trên <html>               │
│  ├─ Lưu vào localStorage("theme")               │
│  └─ Update React context → re-render toggle icon│
└─────────────────────────────────────────────────┘
```

**File thay đổi:**

| File | Thay đổi |
|------|----------|
| `src/styles/global.css` | Thêm block `html[data-theme="dark"] { ... }` với ~40 CSS variable override |
| `src/components/ThemeToggle.tsx` | **Mới** — icon button (☀️/🌙), gọi context |
| `src/contexts/ThemeContext.tsx` | **Mới** — React context + provider, đọc/ghi localStorage, set attribute |
| `src/components/Layout.tsx` | Thêm `<ThemeToggle />` vào header, wrap app bằng `ThemeProvider` |
| `src/App.tsx` | Wrap `<BrowserRouter>` trong `<ThemeProvider>` |

**Dark mode variable mapping (thêm vào `global.css`):**

```css
html[data-theme="dark"] {
  --color-bg: #0f1117;
  --color-bg-accent: #161924;
  --color-surface: #1c1f2e;
  --color-surface-muted: #232738;
  --color-surface-raised: #252a3a;
  --color-border: rgba(255, 255, 255, 0.08);
  --color-border-strong: rgba(255, 255, 255, 0.16);
  --color-text-primary: #e8eaf0;
  --color-text-secondary: #9ba3b5;
  --color-text-muted: #636b7e;
  --color-accent: #6366f1;
  --color-accent-strong: #818cf8;
  --color-accent-light: rgba(99, 102, 241, 0.12);
  --glass-bg: rgba(28, 31, 46, 0.72);
  --glass-border: rgba(255, 255, 255, 0.08);
  --shadow-1: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-2: 0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-3: 0 12px 32px rgba(0, 0, 0, 0.5);
  color-scheme: dark;
}
```

**Transition:** Thêm `transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease` vào `body` và các surface element chính. Không transition tất cả properties vì sẽ gây performance issue.

**Rationale:** Không dùng CSS class toggle (`.dark`) vì `data-theme` attribute:
- Tách biệt concern — attribute chỉ cho styling, không ảnh hưởng component tree
- Dễ query trong CSS: `html[data-theme="dark"] .someClass` nếu cần override cụ thể
- Không cần thêm Zustand/Jotai — `ThemeContext` với `useState` + `useEffect` đủ cho use case này

### D3: Card visual hierarchy — left border + urgency strip

**Quyết định:** Mỗi card có left border 4px color-coded theo `intelligence_tier` và urgency strip 3px ở top cho `critical`/`high`.

**Color mapping:**

| `intelligence_tier` | Left border color | CSS variable |
|---------------------|------------------|--------------|
| `Tactical` | `#ef4444` (red-500) | `--tier-tactical` |
| `Operational` | `#f97316` (orange-500) | `--tier-operational` |
| `Strategic` | `#8b5cf6` (violet-500) | `--tier-strategic` |
| `Informational` | `#94a3b8` (slate-400) | `--tier-informational` |

| `urgency` | Top strip | Behavior |
|-----------|-----------|----------|
| `critical` | `#ef4444` (red) | Strip 3px + subtle pulse animation |
| `high` | `#f97316` (orange) | Strip 3px, static |
| `medium`, `low` | Không có strip | — |

**Cách implement trong `InsightCard.tsx`:**

```tsx
// Tính toán inline style cho dynamic border (tier có thể null)
const tierColor = insight.intelligence_tier
  ? `var(--tier-${insight.intelligence_tier.toLowerCase()})`
  : 'var(--color-border)';

const isUrgent = insight.urgency === 'critical' || insight.urgency === 'high';
```

```css
/* card.module.css */
.card {
  border-left: 4px solid var(--card-tier-color, var(--color-border));
  /* ... existing styles ... */
}

.urgencyStrip {
  height: 3px;
  width: 100%;
  background: var(--card-urgency-color);
}

.urgencyStripCritical {
  animation: urgencyPulse 2s ease-in-out infinite;
}
```

**`so_what` as primary snippet:** Hiện tại `InsightCard.tsx` L27 đã ưu tiên `so_what` rồi (`insight.so_what || insight.signal`), nên không cần thay đổi logic — chỉ cần tăng font-size và prominence trong CSS.

**Hover glow:** Khi hover card, `box-shadow` thay đổi theo tier color:

```css
.card:hover {
  box-shadow: 0 8px 24px var(--card-tier-glow);
}
```

Trong đó `--card-tier-glow` là phiên bản alpha 0.15 của tier color, set qua inline style.

### D4: Filter drawer thay vì dropdown panel

**Quyết định:** Thay thế filter panel hiện tại (expand inline dưới toolbar) bằng slide-in drawer từ bên phải. Giữ preset buttons (🔥 Khẩn cấp, 🇻🇳 Việt Nam, 📈 Đang nổi) inline trên toolbar.

**Lý do chọn drawer thay vì dropdown:**
- 6 filter dimension (tier, urgency, momentum, vietnam, roles, sources) + source search = rất nhiều vertical space
- Dropdown inline đẩy card grid xuống ~300px khi mở, gây jarring scroll
- Drawer overlay không ảnh hưởng layout flow, user có thể scroll filter list dài
- Mobile-friendly hơn — drawer tự nhiên trên touch device

**Cấu trúc drawer:**

```
┌───────────────────────────────────────────────────┐
│ Header: "Bộ lọc nâng cao"          [×] Close     │
├───────────────────────────────────────────────────┤
│ 🔍 Search bar (client-side filter title/summary) │
│                                                    │
│ ═══ Active filters (removable chips) ═══          │
│ [Tactical ×] [Critical ×] [VN: Cao ×]            │
│                                                    │
│ ─── Phân tầng ────────────────────                │
│ ○ Tactical  ○ Operational  ○ Strategic  ○ Info    │
│                                                    │
│ ─── Độ cấp thiết ─────────────────                │
│ ○ Khẩn cấp  ○ Cao  ○ Trung bình  ○ Thấp         │
│                                                    │
│ ─── Xu hướng ─────────────────────                │
│ ○ Mới  ○ Đang nổi  ○ Đã ổn định                  │
│                                                    │
│ ─── Việt Nam ─────────────────────                │
│ ○ Cao  ○ Vừa  ○ Ít                               │
│                                                    │
│ ─── Vai trò ──────────────────────                │
│ ○ Executive  ○ Engineering  ○ Data/AI  ...        │
│                                                    │
│ ─── Nguồn (12/15 active) ────────                 │
│ [Tìm nguồn...]                                    │
│ ○ TechCrunch (42)  ○ The Verge (38)  ...         │
├───────────────────────────────────────────────────┤
│ [Xóa tất cả]                    [Áp dụng (24)]   │
└───────────────────────────────────────────────────┘
```

**Client-side search:** Thêm `searchQuery` state vào `InsightList.tsx`. Filter trên client bằng `String.includes()` trên `title` + `summary_short` + `so_what` sau khi data đã fetch từ API. Không cần API mới.

```tsx
const filteredItems = useMemo(() => {
  if (!searchQuery.trim() || !overviewQuery.data?.items) return overviewQuery.data?.items ?? [];
  const q = searchQuery.toLowerCase();
  return overviewQuery.data.items.filter(item =>
    item.title.toLowerCase().includes(q) ||
    (item.summary_short?.toLowerCase().includes(q)) ||
    (item.so_what?.toLowerCase().includes(q))
  );
}, [searchQuery, overviewQuery.data?.items]);
```

**Result count:** Hiển thị `Đang hiển thị {filteredCount} / {total} bản tin` dưới toolbar, cập nhật realtime khi filter thay đổi.

**Active filter chips:** Dùng chip row ngay dưới toolbar, mỗi chip có nút `×` để remove filter đó. Chip hiện khi bất kỳ filter nào active, kể cả khi drawer đang đóng.

### D5: Detail page — từ 50/50 sang 70/30 layout

**Quyết định:** Thay đổi `detailSplitView` grid từ `1fr 1fr` sang `7fr 3fr`. Original article chuyển từ side-by-side column sang collapsible section bên dưới main content. Sidebar 30% chứa scores + metadata.

**Layout mới:**

```
┌──────────────────────────────────────────────────────────────┐
│ ← Tất cả bản tin  >  Chi tiết bản tin     (Breadcrumb)      │
├──────────────────────────────────────────────────────────────┤
│ [Source pill] • 2 giờ trước                  [🖼 thumbnail]  │
│ Tiêu đề bản tin lớn ở đây                                   │
│ [Tactical] [🔥 Critical] [Rising] [Adopt] [Exec] [Eng] +2   │
├────────────────────────────────────────┬─────────────────────┤
│ 70% — Main Content                    │ 30% — Sidebar       │
│                                        │ (sticky)            │
│ 💡 Ý nghĩa cốt lõi (So What)         │                     │
│ ┌────────────────────────────────┐    │ ┌─────────────────┐ │
│ │ "Nội dung so_what..."         │    │ │ Trust Score     │ │
│ └────────────────────────────────┘    │ │ ████████░░ 8.2  │ │
│                                        │ │                 │ │
│ 🔎 Tóm tắt & Phân tích chi tiết      │ │ Actionability   │ │
│ ┌────────────────────────────────┐    │ │ ██████░░░░ 6.0  │ │
│ │ summary_medium content...     │    │ │                 │ │
│ └────────────────────────────────┘    │ │ Confidence      │ │
│                                        │ │ ███████░░░ 7.5  │ │
│ 📋 Những điều cần biết                │ ├─────────────────┤ │
│ • bullet 1                             │ │ Vai trò         │ │
│ • bullet 2                             │ │ [Exec] [Eng]    │ │
│ • bullet 3                             │ │ [Data/AI]       │ │
│                                        │ ├─────────────────┤ │
│ 👥 Khuyến nghị theo vai trò           │ │ Nguồn gốc       │ │
│ ┌────────────────────────────────┐    │ │ TechCrunch      │ │
│ │ Executive: "..."              │    │ │ [Đọc nguồn ↗]  │ │
│ │ Engineering: "..."            │    │ └─────────────────┘ │
│ └────────────────────────────────┘    │                     │
│                                        │                     │
│ ⚠️ Rủi ro cần lưu ý                  │                     │
│ • risk 1                               │                     │
│ • risk 2                               │                     │
│                                        │                     │
│ 📰 Bài viết gốc (collapsible)  [▼]   │                     │
│ ┌────────────────────────────────┐    │                     │
│ │ (collapsed by default)        │    │                     │
│ └────────────────────────────────┘    │                     │
├────────────────────────────────────────┴─────────────────────┤
│ 🤖 Phân tích tự động bởi Gemini AI                          │
│ Các tin liên quan trong luồng: [ref1] [ref2]                 │
└──────────────────────────────────────────────────────────────┘
```

**Thay đổi cụ thể trong `InsightDetail.tsx`:**
1. Xóa `detailSplitView` / `detailSingleView` conditional — luôn dùng `detailArticleLayout` (70/30)
2. Original article chuyển từ right column (`detailSplitRight`) thành collapsible section trong main content, dùng `OriginalArticlePanel.tsx` component đã có sẵn (hiện chưa import — sẽ tái sử dụng)
3. Thêm sidebar column với scores (trust_score, actionability_score, confidence), roles, source link
4. Sidebar sticky: `position: sticky; top: calc(var(--header-height) + 16px)`
5. Thêm `Breadcrumb.tsx` component — `← Tất cả bản tin > Chi tiết`

**Lưu ý:** `OriginalArticlePanel.tsx` hiện tại KHÔNG được import bởi bất kỳ file nào (đã verify bằng grep). Tuy nhiên component này có logic collapsible sẵn — ta sẽ **tái sử dụng** nó thay vì xóa, rồi refactor inline original article code trong `InsightDetail.tsx` L263–L301 thành dùng component này.

### D6: Animation approach — CSS-first, `requestAnimationFrame` cho counting

**Quyết định:** Ưu tiên CSS animation/transition. Chỉ dùng JavaScript (`requestAnimationFrame`) cho KPI number counting animation.

| Animation | Kỹ thuật | File |
|-----------|----------|------|
| Card entrance stagger | CSS `@keyframes fadeSlideUp` + `animation-delay` set qua inline style, triggered bởi `IntersectionObserver` | `InsightCard.tsx`, `card.module.css` |
| KPI number counting | `requestAnimationFrame` loop từ 0 đến target value trong 800ms, easing `easeOutCubic` | `KPISummary.tsx` |
| Filter chip add/remove | CSS `@keyframes chipBounce` — scale 0.95 → 1.05 → 1.0 trong 200ms | `dashboard.module.css` |
| Scroll-to-top button | CSS `opacity` + `transform` transition, show khi `scrollY > 400px` | `ScrollToTop.tsx` (mới) |
| Card hover glow | CSS `transition: box-shadow 0.2s ease` — đã có, chỉ thay đổi shadow value theo tier color | `card.module.css` |
| Filter drawer slide-in | CSS `transform: translateX(100%) → translateX(0)` + `opacity`, 0.3s ease | `dashboard.module.css` |
| Dark mode transition | CSS `transition: background-color 0.3s, color 0.3s` trên body + surface | `global.css` |

**IntersectionObserver cho card stagger:**

```tsx
// Custom hook useCardEntrance
function useCardEntrance(ref: RefObject<HTMLElement>, index: number) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.animationDelay = `${index * 60}ms`;
          el.classList.add(styles.cardEnter);
          observer.unobserve(el);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, index]);
}
```

**Reducemotion:** Tôn trọng `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  .cardEnter { animation: none; opacity: 1; transform: none; }
  .urgencyStripCritical { animation: none; }
}
```

### D7: Gom Axios instances — single `api/client.ts`

**Quyết định:** Tạo file `src/api/client.ts` export shared Axios instance. Xóa `axios.create()` trùng lặp trong `insights.ts`, `sources.ts`, `stats.ts`.

**Hiện trạng:** 3 file đều tạo instance giống hệt nhau:
```typescript
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});
```

**File mới `src/api/client.ts`:**
```typescript
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});
```

**Migration:**
- `insights.ts`: xóa `const api = axios.create(...)`, thêm `import { apiClient as api } from './client'`
- `sources.ts`: tương tự
- `stats.ts`: tương tự

**Rationale:** Ngoài giảm duplication, shared instance cho phép thêm interceptor sau này (error handling, auth token, request logging) mà chỉ cần sửa 1 file.

### D8: Theme state management — React Context, không Zustand

**Quyết định:** Dùng `React.createContext` + `ThemeProvider` component. Không thêm state management library.

**Lý do:**
- Theme state chỉ có 1 giá trị (`"light" | "dark" | "system"`) — quá đơn giản cho Zustand
- Không cần persistence phức tạp — `localStorage.getItem/setItem` là đủ
- Chỉ 2 consumer: `ThemeToggle.tsx` (đọc + ghi) và `Layout.tsx` (đọc để set initial attribute)
- Project hiện tại không dùng bất kỳ state library nào ngoài TanStack Query (cho server state) — không nên thêm dependency cho 1 boolean

**Context shape:**
```typescript
interface ThemeContextValue {
  theme: 'light' | 'dark' | 'system';
  resolvedTheme: 'light' | 'dark'; // actual applied theme
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}
```

---

## Risks / Trade-offs

### R1: CSS splitting có thể break class references — Rủi ro TRUNG BÌNH

**Mô tả:** Khi tách `insights.module.css`, mọi file import `styles from '../styles/insights.module.css'` sẽ cần update import path. Nếu bỏ sót, class reference sẽ resolve thành `undefined` → element mất styling mà không có runtime error.

**Mitigation:**
- Grep toàn bộ `insights.module.css` import trước khi tách → danh sách chính xác: `InsightCard.tsx`, `InsightList.tsx`, `InsightDetail.tsx`, `ImpactBadge.tsx`, `OriginalArticlePanel.tsx`, `Tooltip.tsx`, `UrgencyBadge.tsx`, `RoleBadge.tsx`, `MomentumIndicator.tsx`, `Pagination.tsx`
- Sau khi tách, chạy TypeScript build (`tsc --noEmit`) — CSS Module type checking sẽ bắt missing classes nếu có `*.module.css.d.ts`
- Visual regression test manual trên cả list page và detail page
- Tách từng nhóm (pagination trước, badges tiếp, card, rồi detail) — mỗi nhóm verify trước khi tiếp

### R2: Dark mode contrast accessibility — Rủi ro TRUNG BÌNH

**Mô tả:** Dark mode color mapping cần đảm bảo WCAG AA contrast ratio (4.5:1 cho text, 3:1 cho large text/UI). Đặc biệt:
- Badge colors (red/orange/green trên dark surface) cần kiểm tra
- Muted text (`--color-text-muted: #636b7e`) trên dark bg có thể dưới 4.5:1
- Gradient backgrounds (hero section, So What card) cần test visibility

**Mitigation:**
- Dùng Chrome DevTools contrast checker cho từng text/background combination
- Test cụ thể: urgency badge red text trên dark surface, tier badge colors, source pill
- Fallback: nếu badge color không đạt contrast, thêm dark-mode-specific override trong `badges.module.css`

### R3: `IntersectionObserver` animation có thể gây jank trên low-end devices — Rủi ro THẤP

**Mô tả:** Card entrance stagger dùng `IntersectionObserver` + CSS animation. Nếu user scroll nhanh qua 12 cards cùng lúc, 12 animation trigger đồng thời có thể gây frame drop.

**Mitigation:**
- Animation chỉ dùng `transform` + `opacity` (GPU-accelerated, không trigger layout/paint)
- `will-change: transform, opacity` chỉ set khi card chưa animated, remove sau khi done
- Tôn trọng `prefers-reduced-motion` — disable animation hoàn toàn
- Stagger delay tối đa 12 × 60ms = 720ms — chấp nhận được

### R4: Filter drawer transition trên mobile — Rủi ro THẤP

**Mô tả:** Drawer slide-in từ phải dùng CSS `transform`. Trên mobile cần:
- Backdrop overlay để block interaction với content bên dưới
- Touch swipe-to-close (nice-to-have, không bắt buộc v1)
- Body scroll lock khi drawer mở

**Mitigation:**
- `overflow: hidden` trên `<body>` khi drawer open (via inline style)
- Backdrop: `position: fixed; inset: 0; background: rgba(0,0,0,0.5)`
- Drawer max-width: `min(420px, 85vw)` — không chiếm hết màn hình
- Close khi click backdrop hoặc nhấn Escape (`useEffect` with `keydown` listener)

### R5: Xóa `ImpactBadge.tsx` — cần verify thêm — Rủi ro THẤP

**Mô tả:** Grep confirm `ImpactBadge` không được import trong bất kỳ file nào ngoài chính nó. Tuy nhiên cần kiểm tra:
- Không có dynamic import (`lazy(() => import(...))`)
- Không có reference trong test files
- Không có plan sử dụng trong tương lai gần

**Mitigation:**
- Đã grep confirm: chỉ có self-reference trong `ImpactBadge.tsx` (interface declaration + export)
- Xóa file, nếu build pass → safe
- Giữ commit riêng cho việc xóa dead code, dễ revert nếu cần

### R6: `OriginalArticlePanel.tsx` — tái sử dụng thay vì xóa

**Mô tả:** Ban đầu proposal liệt kê `OriginalArticlePanel.tsx` là dead code cần xóa. Tuy nhiên sau khi review, component này có collapsible logic hoàn chỉnh (props: `collapsed`, `onToggle`, content rendering) — đúng use case cho detail page redesign (chuyển original article từ side-by-side sang collapsible).

**Quyết định:** Tái sử dụng `OriginalArticlePanel.tsx` trong detail page mới, xóa inline original article code ở `InsightDetail.tsx` L263–L301.

### R7: Warm-tone cleanup có thể vô tình ảnh hưởng visual consistency — Rủi ro THẤP

**Mô tả:** 13 dòng CSS dùng `rgba(120, 99, 77, ...)` nằm rải rác trong pagination, detail body, original panel, spinner. Thay thế bằng `var(--color-border)` hoặc `var(--color-border-strong)` sẽ hơi khác visual nhưng consistent hơn với palette.

**Mitigation:**
- Mapping thủ công cho từng instance:
  - `rgba(120, 99, 77, 0.12–0.16)` → `var(--color-border)` (hiện là `rgba(15, 23, 42, 0.08)` — hơi nhạt hơn, cần test)
  - `rgba(120, 99, 77, 0.2)` → `var(--color-border-strong)` (hiện là `rgba(15, 23, 42, 0.16)`)
  - `rgba(255, 251, 246, 0.96)` (warm white bg) → `var(--color-surface)` (pure white `#ffffff`)
- So sánh visual trước/sau trên pagination và detail page

---

## Phụ lục: File inventory thay đổi

### Files mới tạo

| File | Mục đích |
|------|----------|
| `src/styles/card.module.css` | CSS Module cho InsightCard |
| `src/styles/detail.module.css` | CSS Module cho InsightDetail |
| `src/styles/badges.module.css` | CSS Module cho badge/pill components |
| `src/styles/pagination.module.css` | CSS Module cho Pagination |
| `src/styles/list.module.css` | CSS Module cho InsightList page |
| `src/api/client.ts` | Shared Axios instance |
| `src/components/ThemeToggle.tsx` | Dark mode toggle button |
| `src/components/ScrollToTop.tsx` | Scroll-to-top FAB |
| `src/components/Breadcrumb.tsx` | Breadcrumb navigation |
| `src/contexts/ThemeContext.tsx` | Theme context + provider |

### Files sửa đổi

| File | Thay đổi chính |
|------|----------------|
| `src/styles/global.css` | Thêm `html[data-theme="dark"]` block, tier color variables, body transition |
| `src/styles/insights.module.css` | Xóa CSS đã migrate, giữ lại comment deprecation |
| `src/styles/dashboard.module.css` | Thêm filter drawer styles, chip animation, search bar styles |
| `src/components/InsightCard.tsx` | Left border + urgency strip, entrance animation, import card.module.css |
| `src/components/KPISummary.tsx` | Number counting animation với requestAnimationFrame |
| `src/components/Layout.tsx` | Thêm ThemeToggle, ThemeProvider |
| `src/pages/InsightList.tsx` | Filter drawer, search bar, result count, active chips |
| `src/pages/InsightDetail.tsx` | 70/30 layout, collapsible original article, sticky sidebar, Breadcrumb |
| `src/api/insights.ts` | Import shared client |
| `src/api/sources.ts` | Import shared client |
| `src/api/stats.ts` | Import shared client |
| `src/App.tsx` | Wrap ThemeProvider |

### Files xóa

| File | Lý do |
|------|-------|
| `src/components/ImpactBadge.tsx` | Dead code — không được import bởi bất kỳ file nào |
| `src/styles/insights.module.css` | Xóa ở cuối sau khi verify hoàn tất migration (cuối cùng) |
