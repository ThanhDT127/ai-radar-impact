## Context

AI Radar Impact Dashboard hiện có ~1.300 dòng CSS (insights.module.css + dashboard.module.css), 16 components, 2 pages. Giao diện dùng warm-earth palette (Manrope + Space Grotesk, accent `#b84d1e`) nhưng đã trải qua 6+ lần patch UI nhỏ liên tiếp nên thiếu nhất quán.

**Trạng thái hiện tại:**
- KPI cards: 4 ô grid cơ bản, chỉ có số + tooltip, không có trend/sparkline
- Filter Panel: ẩn/hiện panel khi bấm nút, thiếu visual compact
- Insight Cards: layout đồng đều (3-col grid), thiếu featured/hero card
- Detail Page: split-view 50/50 (AI bên trái, bài gốc bên phải), nặng về text
- Design tokens: tán loạn trong `global.css` (~22 CSS variables), thiếu spacing/elevation scale
- Không có dark mode

**Module bị ảnh hưởng:** M6 (Dashboard)

## Goals / Non-Goals

**Goals:**
- Tạo design system chính thức (tokens, typography scale, spacing, elevation) chuẩn hóa toàn bộ UI
- Redesign KPI cards: thêm trend indicators (▲▼), color-coding theo direction, subtitle rõ nghĩa
- Redesign Filter Panel: compact horizontal bar always-visible, không ẩn/hiện toggle
- Redesign Insight Cards: featured hero card (card đầu lớn hơn) + standard grid
- Redesign Detail Page: article-style layout, hero image header, collapsible original content
- Nâng cấp typography: chuyển từ Manrope sang Inter (dễ đọc hơn ở kích thước nhỏ)
- Thêm micro-interactions: hover states, press states, smooth transitions
- Responsive polish cho tablet (768px) và mobile (375px)
- Visual QA tự động qua Chrome DevTools MCP

**Non-Goals:**
- Không thêm chart library nặng (D3.js, Recharts) — chỉ CSS sparklines/bars
- Không thay đổi backend API logic — chỉ thêm `primary_image` vào InsightListItem
- Không xây dark mode trong lần này (chỉ chuẩn bị token structure sẵn)
- Không thay đổi routing structure
- Không xây sidebar navigation — giữ top-bar hiện tại

## Decisions

### 1. Typography System
```
Font stack: Inter (body) + Space Grotesk (display) + JetBrains Mono (code/scores)
Type scale:  xs (0.75rem) → sm (0.8rem) → base (0.88rem) → md (1rem) 
             → lg (1.25rem) → xl (1.5rem) → 2xl (2rem) → 3xl (3rem)
```
Lý do: Inter có x-height cao hơn Manrope, đọc tốt hơn ở 12-14px — kích thước phổ biến trên dashboard.

### 2. Color Palette (giữ warm-earth nhưng modernize)
```
Primary accent: #c25520 → gradient (#c25520 → #e67a3e)  
Semantic:  
  success: #16a34a (xanh lá, mạnh hơn)
  danger:  #dc2626 (đỏ, rõ ràng hơn)
  warning: #ca8a04 (vàng đậm)
  info:    #2563eb (xanh dương)
Surface:   #faf8f5 (warm white) → #f5f0ea (warm muted)
Text:      #1a1410 (primary) → #5c4d3f (secondary) → #9a8a79 (muted)
```

### 3. Spacing Scale (8px base)
```
0: 0 | 1: 4px | 2: 8px | 3: 12px | 4: 16px | 5: 20px | 6: 24px 
8: 32px | 10: 40px | 12: 48px | 16: 64px | 20: 80px
```

### 4. Elevation System
```
Level 0: none (flat)
Level 1: 0 1px 3px rgba(0,0,0,0.04)          — cards
Level 2: 0 4px 12px rgba(0,0,0,0.06)          — raised
Level 3: 0 8px 24px rgba(0,0,0,0.08)          — modals, drawers
Level 4: 0 16px 48px rgba(0,0,0,0.12)         — overlays
```

### 5. InsightList Layout Architecture
```
┌──────────────────────────────────────────┐
│  Header (sticky): logo + search + nav    │
├──────────────────────────────────────────┤
│  Hero Banner (condensed)                 │
├──────────────────────────────────────────┤
│  KPI Strip: [📊 Total] [🔴 Critical] [✅ Opp] [📡 Sources] │
├──────────────────────────────────────────┤
│  Filter Bar: Sort ▾ | 🔥 Khẩn | 🇻🇳 VN | 📈 Nổi | ⚙ More filters... │
├──────────────────────────────────────────┤
│  ┌──────────────────┐  ┌────┐  ┌────┐   │
│  │  FEATURED CARD   │  │ 2  │  │ 3  │   │
│  │  (2x height)     │  │    │  │    │   │
│  │                  │  ├────┤  ├────┤   │
│  │                  │  │ 4  │  │ 5  │   │
│  └──────────────────┘  └────┘  └────┘   │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐           │
│  │ 6  │ │ 7  │ │ 8  │ │ 9  │  ...      │
│  └────┘ └────┘ └────┘ └────┘           │
├──────────────────────────────────────────┤
│  Pagination / Load More                  │
└──────────────────────────────────────────┘
```

### 6. InsightDetail Layout Architecture
```
┌──────────────────────────────────────────┐
│  ← Tất cả bản tin   Breadcrumb          │
├──────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐│
│  │  HERO IMAGE (full-width, gradient)   ││
│  │  Title overlay + badges + time       ││
│  └──────────────────────────────────────┘│
│  ┌───────────────────────┐ ┌───────────┐│
│  │  AI Summary (main)    │ │ Sidebar   ││
│  │  • Bullets            │ │ Scores    ││
│  │  • So What            │ │ Roles     ││
│  │  • Recommendations    │ │ Actions   ││
│  │  • Risks              │ │ Topics    ││
│  │  • Deep Analysis      │ │ Timeline  ││
│  └───────────────────────┘ └───────────┘│
│  ┌──────────────────────────────────────┐│
│  │  ▶ Xem bài viết gốc (collapsible)   ││
│  │  [Original article text content]     ││
│  └──────────────────────────────────────┘│
│  ┌──────────────────────────────────────┐│
│  │  Related Insights (horizontal scroll)││
│  └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

### 7. API Endpoints bị ảnh hưởng

| Method | Endpoint | Thay đổi |
|--------|----------|----------|
| GET | `/api/v1/insights` | Thêm `primary_image` vào InsightListItem response |
| GET | `/api/v1/insights/{id}` | Không đổi (đã có `primary_image`, `content_text`) |
| GET | `/api/v1/stats` | Thêm `trend_direction` và `previous_total` cho KPI trend |

### 8. DB Tables bị ảnh hưởng
Không có migration mới — `primary_image` được extract động từ `raw_documents.raw_content` (regex og:image / twitter:image) tại runtime.

## Risks / Trade-offs

1. **CSS Regression Risk (Medium)**: Thay đổi lớn CSS module có thể break existing layouts. **Mitigation**: Viết CSS mới song song, swap in từng component, test qua Chrome DevTools screenshots.

2. **Performance Impact (Low)**: Featured card + hero image thêm load thời gian. **Mitigation**: Lazy-load images, CSS `content-visibility: auto`.

3. **Font Change Impact (Low)**: Chuyển Manrope → Inter ảnh hưởng toàn bộ text metrics. **Mitigation**: Inter và Manrope gần giống nhau về x-height, chỉ cần adjust line-height nhỏ.

4. **primary_image trong List API (Low)**: Thêm regex extraction trong serialization. **Mitigation**: Chỉ chạy regex khi cần, cached per-request.
