## Context

Dashboard hiện có ~10 loại badge/indicator (UrgencyBadge, ImpactBadge, MomentumIndicator, RoleBadge, tier badges, topic tags, event tags, trust score, actionability score, adoption ring) nhưng KHÔNG CÓ tooltip nào giải thích cho user. Một số component dùng `title=""` attribute native (chậm 1s, xấu, không customizable).

Cần hệ thống tooltip thống nhất: 1 component, 1 registry nội dung, áp dụng cho tất cả.

## Goals / Non-Goals

**Goals:**
- Tạo `<Tooltip>` component: hover → popup với nội dung tiếng Việt giải thích chi tiết
- Centralized registry (`TOOLTIP_CONTENT`) cho tất cả nội dung chú thích — dễ maintain
- Wrap tất cả badges hiện có bằng Tooltip
- CSS Module cho tooltip (không thêm dependency ngoài)
- Accessible: `aria-describedby` cho screen readers

**Non-Goals:**
- Không hỗ trợ touch/mobile (dùng CSS `@media (hover: hover)` để skip trên mobile)
- Không thêm tooltip cho KPI cards (change riêng)
- Không thay đổi layout/structure của components hiện tại
- Không dùng thư viện ngoài (Tippy.js, Floating UI) — tự build, ~80 LOC

## Decisions

### 1. Pure CSS + React Portal approach
Dùng React Portal render tooltip vào `document.body` để tránh overflow issues. Position tính bằng `getBoundingClientRect()`.

**Rationale:** Nhẹ, không dependency, đủ cho use case đơn giản (text-only tooltip, 1 direction).

### 2. Content Registry pattern
```typescript
// TooltipContent.ts
export const TOOLTIP_CONTENT = {
  tier: {
    Strategic: "Bài mang tính chiến lược — xu hướng dài hạn, cần theo dõi...",
    Tactical: "Bài có thể hành động ngay — tool mới, bản vá bảo mật...",
    ...
  },
  urgency: { critical: "...", high: "...", ... },
  score: { actionability: "...", trust: "..." },
  ...
} as const;
```
**Rationale:** Centralized content → dễ cập nhật text, dễ i18n sau nếu cần.

### 3. Wrapping strategy: Tooltip wraps badge, không sửa nội bộ badge
```tsx
<Tooltip content={TOOLTIP_CONTENT.tier.Strategic}>
  <span className={styles.tierBadge}>Strategic</span>
</Tooltip>
```
**Rationale:** Không phải sửa logic bên trong từng badge component. Tooltip là layer bên ngoài.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Tooltip bị cắt bởi card overflow | Dùng React Portal → render ở body level |
| Nhiều tooltip cùng lúc (hover nhanh) | Chỉ cho 1 tooltip active, debounce 200ms |
| Performance với 36 cards × 5 tooltips/card | Tooltip chỉ mount khi hover, không pre-render |
| Tooltip trên mobile vô dụng | `@media (hover: hover)` — chỉ hiện trên desktop |

## Module ảnh hưởng
- **M6: Dashboard** — chỉ frontend, không ảnh hưởng backend/API/DB
- **API endpoints**: Không thay đổi
- **Bảng DB**: Không thay đổi
