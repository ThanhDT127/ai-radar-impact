## Why

Giao diện hiện tại của AI Radar Impact Dashboard đã trải qua nhiều lần chỉnh sửa tăng dần (incremental patches) qua 6+ changes nhỏ liên tiếp, dẫn đến:

1. **Thiếu nhất quán về thiết kế**: CSS module phình lên 1.200+ dòng, styles chồng chéo, không có design system rõ ràng. Các component được thiết kế theo kiểu "vá lỗi" thay vì theo một hệ thống visual nhất quán.
2. **UX chưa đạt chuẩn dashboard chuyên nghiệp**: Bố cục grid đơn giản, thiếu visual hierarchy, thiếu data visualization (charts, sparklines), KPI cards chưa có xu hướng (trend arrows). Giao diện giống blog hơn là một intelligence dashboard.
3. **Thiếu responsive polish**: Breakpoints cơ bản nhưng chưa tối ưu cho tablet/mobile, filter panel chiếm quá nhiều không gian, navigation tĩnh.
4. **Trang chi tiết rời rạc**: Split-view hiện tại hoạt động nhưng thiếu polish — bài gốc chỉ là text thô, thiếu section navigation, thiếu reading progress.

Mục tiêu: Redesign toàn bộ thành một **premium intelligence dashboard** đạt chuẩn thẩm mỹ hiện đại, lấy cảm hứng từ các sản phẩm như Linear, Notion, Bloomberg Terminal (phiên bản sáng) — nhưng giữ nguyên Vietnamese-first UX.

## What Changes

### Design System & Tokens
- Tạo design system file chính thức với semantic color tokens, spacing scale, typography scale, elevation system
- Chuyển từ warm-earth palette hiện tại sang palette hiện đại hơn nhưng vẫn giữ sự ấm áp
- Thêm dark mode support (CSS custom properties toggle)
- Standardize border-radius, shadow, spacing scales

### Trang chính (InsightList)
- Redesign KPI cards: thêm sparkline/mini-chart, trend indicator (↑↓), comparison vs. tuần trước
- Redesign Filter Panel: compact horizontal bar thay vì panel ẩn/hiện — always-visible, chip-based
- Redesign Insight Cards: layout 2-column với featured card lớn ở trên, card grid bên dưới
- Thêm "Quick View" drawer: click card → slide-in panel thay vì chuyển trang ngay
- Sticky header với search bar và breadcrumb navigation

### Trang chi tiết (InsightDetail)
- Full-width hero header với featured image, gradient overlay, metadata badges
- Article-style reading layout cho AI summary (trái) + sidebar (phải) thay vì split 50/50
- Bài gốc hiển thị trong collapsible section phía dưới thay vì cột phải
- Sticky sidebar cho scores, recommendations, actions

### Components
- Redesign toàn bộ badge system (UrgencyBadge, ImpactBadge, TierBadge, RoleBadge) theo glassmorphism style
- Tooltip nâng cấp: rich tooltip với icon, gradient header
- Pagination: infinite scroll option + page indicator
- Layout: thêm sidebar navigation

## Capabilities

### New Capabilities
- `dashboard-design-system`: Design system chính thức cho AI Radar Impact — tokens, typography, colors, elevation, spacing scale
- `dashboard-premium-layout`: Layout premium cho InsightList — hero KPI, featured card, compact filters, quick-view drawer
- `dashboard-detail-redesign`: Redesign InsightDetail — hero header, article layout, collapsible original content, sticky sidebar

### Modified Capabilities
- `insight-dashboard`: Thay đổi cấu trúc layout chính, card design, filter UX, pagination behavior

## Impact

- **Frontend files bị ảnh hưởng**: `global.css`, `insights.module.css`, `dashboard.module.css`, toàn bộ 16 component files, 2 page files
- **Backend**: Không thay đổi logic — chỉ cần thêm `primary_image` vào InsightListItem schema (đã có ở Detail)
- **Dependencies**: Google Fonts (Inter, JetBrains Mono), không thêm thư viện JS mới
- **Risk**: Thay đổi CSS lớn có thể gây regression — cần visual testing kỹ qua Chrome DevTools MCP
- **Phase**: Phase 1 — cải thiện dashboard MVP hiện tại
