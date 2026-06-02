## Why

Dashboard hiện tại có nhiều vấn đề UX nghiêm trọng ảnh hưởng đến khả năng đọc và tiếp cận thông tin:

1. **Ảnh hero làm nền che chữ** — Detail page dùng ảnh bài viết làm background overlay, badges và title bị ảnh che mất, đặc biệt với ảnh sáng màu.
2. **Thiếu split view song ngữ** — Bản dịch AI (tiếng Việt) và bài gốc (tiếng Anh) không hiển thị cạnh nhau, phải scroll hoặc click mở riêng, không đối chiếu được.
3. **Metadata sidebar quá nhiều cards** — 6 cards riêng biệt (Điểm đánh giá, Thông tin, Vai trò, Chủ đề, Chỉ số thực tế, Dòng thời gian) chiếm quá nhiều diện tích, phải scroll nhiều mới đọc hết.
4. **List page: cards không đều** — Featured card 2-col chiếm diện tích khổng lồ khi không có ảnh, chỉ hiện icon placeholder trống rỗng.
5. **Thiếu `primary_image` trong list API** — Backend đã extract ảnh nhưng Pydantic schema `InsightListItem` thiếu field → tất cả cards không có ảnh.

Đây là change Phase 1, thuộc module M6 (Dashboard).

## What Changes

### Detail Page — Bỏ hero background, thêm split view

- **Header compact**: Ảnh chuyển thành thumbnail inline (120×80px) cạnh title, không còn là hero background
- **Summary (so_what) lên đầu** ngay dưới title — thông tin quan trọng nhất ở vị trí scan nhanh
- **Metadata ribbon inline**: Gộp 6 sidebar cards thành 1 block compact (scores + info + roles + topics + indicators)
- **Split view 50/50**: Cột trái = AI content tiếng Việt (bullets, phân tích, khuyến nghị, rủi ro), cột phải = bài gốc tiếng Anh (luôn hiện, scroll độc lập)
- **Bỏ hẳn sidebar 30%** — không còn layout 70/30

### List Page — Cards đồng đều, ảnh thumbnail

- Bỏ featured card (2-col span) → tất cả cards cùng kích thước
- Ảnh chuyển thành thumbnail nhỏ inline thay vì container 16:9
- Thêm `onError` handler cho `<img>` — fallback ẩn ảnh khi lỗi
- Cards không có ảnh: ẩn hẳn image container, không hiện placeholder icon

### Backend — Thêm `primary_image` vào InsightListItem

- Thêm 1 dòng `primary_image: str | None = None` vào Pydantic schema

## Capabilities

### New Capabilities
- `split-view-detail`: Hiển thị bản dịch AI và bài gốc song song 50/50 trên detail page
- `compact-metadata-ribbon`: Gộp 6 sidebar cards thành 1 dải metadata inline compact

### Modified Capabilities
- `insight-card-display`: Cards đồng đều, ảnh thumbnail inline, bỏ featured layout
- `insight-detail-layout`: Bỏ hero background, header compact, split view thay sidebar

## Non-goals

- Không thay đổi logic AI pipeline hoặc phân tích nội dung
- Không thay đổi filter/search/sort functionality
- Không thay đổi API endpoints (chỉ thêm field vào schema)
- Không responsive mobile trong scope này (sẽ là change riêng)

## Impact

- **Frontend**: `InsightDetail.tsx`, `InsightCard.tsx`, `InsightList.tsx`, `OriginalArticlePanel.tsx`, `insights.module.css`, `dashboard.module.css`
- **Backend**: `backend/app/schemas/insight.py` (1 dòng)
- **Dependencies**: Không có dependency mới
- **Breaking changes**: Không — chỉ thay đổi UI rendering, API backward-compatible
