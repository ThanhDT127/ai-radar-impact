## Why

Dashboard hiện tại trông "xấu xấu" — không phải do bug mà do **visual identity thiếu tính cách**:

1. **Color palette Warm Earth (#f5f1eb / #c25520)** tạo cảm giác "café menu" thay vì tech intelligence dashboard. Mọi thứ đều nâu, thiếu tương phản nhiệt độ cool/warm.
2. **Font system generic** — Inter là font an toàn nhưng thiếu personality cho một sản phẩm AI intelligence.
3. **Cards = wall of text** — 6-7 badges + 3 bullets + 2 titles trên mỗi card, không có visual anchor nào nổi bật.
4. **Zero depth** — shadow-1 gần vô hình, không glassmorphism thực sự, mọi element cùng 1 elevation → phẳng lì.
5. **Badge soup** — 9 kiểu badge khác nhau trên metadata ribbon, gây visual noise thay vì truyền tải thông tin.

Đây là change Phase 1, module M6 (Dashboard). Hướng thiết kế: **Clean Editorial + Modern SaaS** (The Verge meets Linear).

## What Changes

### Color Palette — Cool Neutral thay Warm Earth
- Background chuyển sang cool-neutral (#f8f9fb) thay vì kem nâu (#f5f1eb)
- Surface cards: true white (#ffffff) với shadow rõ ràng hơn
- Accent chính: Indigo (#4f46e5) — sharp, professional, tech-native
- Accent phụ: Amber (#f59e0b) cho urgency/warning — giữ warmth có chủ đích
- Text: Near-black (#111827) trên nền sáng, tăng contrast

### Font System — Từ generic → distinctive
- Display font: Satoshi hoặc Plus Jakarta Sans thay Space Grotesk — geometric nhưng ấm hơn
- Body font: Geist hoặc giữ Inter — optimized cho readability
- Mono: JetBrains Mono (giữ nguyên)

### Card Visual — Từ text wall → scannable
- Giảm thông tin trên card: chỉ giữ title + 1 line summary + source/time + 1 urgency badge
- Bỏ bullets trên card list (chuyển vào detail page)
- Thumbnail lớn hơn hoặc ẩn hẳn nếu không có ảnh
- Shadow bolder: shadow-2 mặc định, shadow-3 on hover

### Badge System — Từ soup → hierarchy
- Mỗi card chỉ hiển thị tối đa 3 indicators: urgency/impact + tier + 1 topic
- Detail page ribbon: compact hơn, ít section labels

## Capabilities

### New Capabilities
- `cool-neutral-palette`: Hệ màu cool-neutral mới cho toàn bộ dashboard
- `typography-system`: Font display + body mới, tăng personality và readability

### Modified Capabilities
- `insight-card-display`: Cards tối giản hơn, bỏ bullets, chỉ giữ thông tin essential
- `insight-detail-layout`: Ribbon metadata compact, badge hierarchy rõ ràng hơn

## Non-goals

- Không thay đổi AI pipeline, backend logic, API endpoints
- Không làm dark mode (sẽ là change riêng sau khi palette mới ổn định)
- Không thêm sidebar navigation (giữ top header layout hiện tại)
- Không redesign filter/search UI trong scope này

## Impact

- **Frontend**: `global.css` (tokens), `insights.module.css`, `InsightCard.tsx`, `InsightDetail.tsx`, `InsightList.tsx`, `index.html` (font imports)
- **Backend**: Không thay đổi
- **Dependencies**: Google Fonts mới (Satoshi/Plus Jakarta Sans + Geist)
- **Breaking changes**: Không — chỉ visual, backward-compatible
