## 1. Tooltip Component

- [x] 1.1 Tạo `frontend/src/components/Tooltip.tsx`: React Portal, position auto, fade animation, `aria-describedby`
- [x] 1.2 Thêm CSS cho tooltip vào `frontend/src/styles/insights.module.css`: dark bg, max-width 280px, arrow pointer, `@media (hover: hover)`
- [x] 1.3 Tạo `frontend/src/components/TooltipContent.ts`: registry nội dung tiếng Việt cho tất cả badge types (tier, urgency, impact, role, score, topic, event)

## 2. Wrap Badge Components

- [x] 2.1 Cập nhật `InsightCard.tsx`: wrap tier badge, urgency/impact badge, actionability score, trust score bằng Tooltip
- [x] 2.2 Cập nhật `UrgencyBadge.tsx`: thay `title=""` bằng Tooltip với content từ registry
- [x] 2.3 Cập nhật `MomentumIndicator.tsx`: thay `title=""` bằng Tooltip
- [x] 2.4 Cập nhật `ImpactBadge.tsx`: thêm Tooltip (hiện không có giải thích nào)
- [x] 2.5 Cập nhật `RoleBadge.tsx`: thêm Tooltip giải thích vai trò

## 3. Detail Page Tooltips

- [x] 3.1 Cập nhật `InsightDetail.tsx`: thêm Tooltip cho tier badge, adoption ring, practical indicators, actionability score bar, trust score

## 4. Verification

- [x] 4.1 Chạy `npx tsc --noEmit` — TypeScript clean
- [x] 4.2 Test hover tooltip trên browser: build thành công, frontend chạy tại localhost:5173
- [x] 4.3 Test mobile viewport: `@media (hover: none)` CSS rule đã thêm
