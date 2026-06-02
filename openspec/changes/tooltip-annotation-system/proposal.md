## Why

Hiện tại toàn bộ UI không có hệ thống chú thích (annotation). Người dùng nhìn vào dashboard thấy các badge (Strategic, Tactical, Critical, Cao), score (⚡ 73%, 🛡️ 80%), KPI cards (1.251, 102, 667, 62) mà không hiểu chúng nghĩa gì. Các `title` attribute native của browser chậm (1s delay), xấu, và không đủ chi tiết.

Đây là **foundation component** — tất cả các change UI tiếp theo (KPI upgrade, card redesign, detail split-view) đều cần Tooltip để giải thích ngữ cảnh cho người dùng.

## What Changes

1. Tạo component `<Tooltip>` tái sử dụng: hover 200ms → popup đẹp, tiếng Việt, max 280px
2. Tạo registry `TOOLTIP_CONTENT` chứa tất cả nội dung chú thích (centralized, dễ maintain)
3. Wrap tất cả badges hiện tại (ImpactBadge, UrgencyBadge, MomentumIndicator, RoleBadge, tier badges, topic/event tags) bằng Tooltip
4. Thay thế tất cả `title=""` attribute bằng Tooltip component

## Capabilities

### New Capabilities
- `tooltip-system`: Component Tooltip tái sử dụng với positioning tự động, fade-in animation, và content registry tiếng Việt cho tất cả UI elements

### Modified Capabilities
_(Không có thay đổi requirements ở spec level)_

## Impact

**Frontend files bị ảnh hưởng:**
- `components/Tooltip.tsx` — [NEW] Component chính
- `components/TooltipContent.ts` — [NEW] Registry nội dung chú thích
- `components/ImpactBadge.tsx` — Wrap bằng Tooltip
- `components/UrgencyBadge.tsx` — Thay `title` bằng Tooltip
- `components/MomentumIndicator.tsx` — Thay `title` bằng Tooltip
- `components/RoleBadge.tsx` — Thêm Tooltip giải thích vai trò
- `components/InsightCard.tsx` — Tooltip cho tier badge, actionability score, trust score
- `styles/insights.module.css` — CSS cho tooltip popup

**Non-goals:**
- Không thay đổi layout card hay detail page (change riêng)
- Không thêm tooltip cho KPI cards (change riêng: kpi-cards-upgrade)
- Không mobile touch support (Phase 2)

**Phase:** Phase 1 — áp dụng ngay
