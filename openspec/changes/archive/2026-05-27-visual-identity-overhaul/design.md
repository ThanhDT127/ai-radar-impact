## Context

Dashboard AI Radar Impact hiện đang dùng palette Warm Earth tone (#f5f1eb background, #c25520 accent) với font Inter/Space Grotesk. Giao diện trông "nhạt nhẽo" — thiếu tương phản, thiếu depth, cards quá nhiều text và badges. Cần overhaul visual identity sang hướng Clean Editorial + Modern SaaS để phù hợp hơn với sản phẩm AI intelligence cho developer/leader.

## Goals / Non-Goals

**Goals:**
- Chuyển color palette sang cool-neutral — professional, tech-native
- Đổi font display sang geometric sans-serif có personality hơn
- Giảm visual noise trên cards — fewer badges, bolder hierarchy
- Tăng depth với shadow system mạnh hơn
- Tạo brand identity rõ ràng cho sản phẩm AI

**Non-Goals:**
- Không làm dark mode (change riêng)
- Không restructure layout (split view, card grid giữ nguyên)
- Không đổi backend/API

## Decisions

### 1. Color Palette: Cool Neutral

```css
/* ── BỎ toàn bộ Warm Earth ── */

/* ── THAY BẰNG Cool Neutral ── */
--color-bg: #f8f9fb;                    /* Cool off-white, hơi xanh */
--color-bg-accent: #f1f3f9;             /* Subtle lavender tint */
--color-surface: #ffffff;               /* True white cards */
--color-surface-muted: #f5f6fa;
--color-surface-raised: #ffffff;
--color-border: rgba(15, 23, 42, 0.08); /* Slate-based borders */
--color-border-strong: rgba(15, 23, 42, 0.16);

--color-text-primary: #111827;          /* Near-black, max contrast */
--color-text-secondary: #4b5563;        /* Gray-600 */
--color-text-muted: #9ca3af;            /* Gray-400 */

--color-accent: #4f46e5;               /* Indigo-600 — primary brand */
--color-accent-strong: #4338ca;        /* Indigo-700 */
--color-accent-light: rgba(79, 70, 229, 0.08);
--color-accent-gradient: linear-gradient(135deg, #4f46e5, #7c3aed);

/* Warmth chỉ dùng cho urgency/warning — có chủ đích */
--color-warning: #f59e0b;              /* Amber */
--color-danger: #ef4444;               /* Red */
--color-success: #10b981;              /* Emerald */
--color-info: #3b82f6;                 /* Blue */
```

Lý do:
- Indigo (#4f46e5) là màu "AI/tech" phổ biến nhất (Linear, Vercel, Stripe)
- Cool background tạo tương phản mạnh với white cards → depth tự nhiên
- Giữ amber/red cho semantic colors → warmth chỉ xuất hiện khi cần nhấn mạnh

### 2. Typography System

```css
/* ── Font Families ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Geist:wght@400;500;600&display=swap');

--font-display: 'Plus Jakarta Sans', sans-serif;
--font-body: 'Geist', 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', ui-monospace, monospace;
```

| Font | Vai trò | Lý do chọn |
|------|---------|------------|
| **Plus Jakarta Sans** | Display (titles, headers) | Geometric, friendly nhưng professional. Nét tròn hơn Space Grotesk, personality rõ ràng. Google Fonts free. |
| **Geist** | Body text | Designed by Vercel cho readability. Neutral nhưng modern, x-height lớn. Nếu Geist không load → fallback Inter. |
| **JetBrains Mono** | Code, badges | Giữ nguyên — đã tốt |

Fallback plan: Nếu Geist chưa có trên Google Fonts (hiện trên npm), dùng Inter làm body và chỉ đổi Display sang Plus Jakarta Sans. Impact vẫn đáng kể vì headers là nơi mắt nhìn trước.

### 3. Shadow System — Tăng depth

```css
/* ── Shadows — Bolder, cooler ── */
--shadow-1: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
--shadow-2: 0 4px 16px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04);
--shadow-3: 0 12px 32px rgba(0, 0, 0, 0.08), 0 4px 8px rgba(0, 0, 0, 0.04);
--shadow-4: 0 24px 64px rgba(0, 0, 0, 0.12), 0 8px 16px rgba(0, 0, 0, 0.06);

/* Cards: shadow-2 default, shadow-3 hover */
/* Hero/Stats: shadow-1 */
```

### 4. Card Redesign — Scannable

**Hiện tại (7+ elements):**
- Source pill + time
- Title (Vietnamese)
- Original title (English, muted)
- 3-5 tag badges
- 3 bullet points
- Urgency badge footer

**Mới (4 elements max):**
- Source + time (inline, subtle)
- Title only (no original title on card)
- 1 urgency/impact badge + 1 tier badge (max 2 badges)
- 1-line summary snippet (thay vì bullets)
- Thumbnail nếu có (giữ 120×84)

```
┌──────────────────────────────────────┐
│  Source  ·  2 giờ trước              │
│                                      │
│  Tiêu đề bài viết đã         ┌────┐ │
│  được dịch sang tiếng Việt    │ 📸 │ │
│  rõ ràng, dễ hiểu             └────┘ │
│                                      │
│  Một dòng tóm tắt ngắn gọn...       │
│                                      │
│  ⚡ Khẩn cấp  ·  TACTICAL            │
└──────────────────────────────────────┘
```

### 5. Detail Page Ribbon — Compact

Giữ metadata ribbon nhưng bỏ section labels ("PHÂN LOẠI", "ĐỐI TƯỢNG", "CHỦ ĐỀ"). Thay bằng badges tự giải thích, xếp ngang liên tục trên 1 dòng:

```
┌──────────────────────────────────────────────────────────┐
│ TACTICAL │ ⚡Khẩn cấp │ 🌱Mới │ Security │ Dev │ AI/ML  │
└──────────────────────────────────────────────────────────┘
```

### 6. Glassmorphism & Micro-interactions

- Hero section: subtle gradient mesh background (indigo → purple → blue, opacity 5-10%)
- Stats cards: slight glass effect với backdrop-filter
- Card hover: translateY(-6px) + shadow-3 + border-color accent (indigo)
- Badge hover: subtle scale(1.02)

## Risks / Trade-offs

- **Font load time**: Plus Jakarta Sans + Geist = ~2 font loads thêm. Mitigate bằng `display=swap` và preload hints.
- **Geist availability**: Geist font có thể không available trên Google Fonts. Fallback: dùng Inter cho body, chỉ đổi display font. Impact vẫn rất lớn.
- **Color contrast**: Indigo trên white đạt WCAG AA (contrast ratio 5.74:1). Đã verify.
- **Brand consistency**: Đổi palette triệt để sẽ thay đổi "nhận diện" hoàn toàn. Nhưng nhận diện hiện tại là "xấu" theo user → đổi là đúng.
