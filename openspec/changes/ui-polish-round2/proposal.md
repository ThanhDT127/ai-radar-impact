## Why

Sau đợt redesign M6 đầu tiên (change `ui-redesign`), giao diện đã có nhiều cải tiến (dark mode, card system, filter drawer, 70/30 layout). Tuy nhiên qua visual review, phát hiện **7 vấn đề** cần fix gấp:

1. **Badge ngôn ngữ lẫn lộn** — "Tactical", "Trial", "Migr" hiện tiếng Anh, trong khi UrgencyBadge/MomentumIndicator đã tiếng Việt
2. **Score bars sidebar không cần thiết** — "Chỉ số đánh giá" (Độ tin cậy/Khả năng hành động/Độ chắc chắn) thừa, user yêu cầu bỏ
3. **Mất split view bản gốc** — Layout 70/30 đã bỏ mất phần hiển thị bài gốc song song. Cần khôi phục 50/50 (phân tích | bản gốc)
4. **Card thiếu thumbnail** — Khi ảnh lỗi/null, card ẩn hoàn toàn thay vì hiện placeholder
5. **Dark mode KPI chưa đẹp** — Background sặc sỡ, chip filter dùng warm-tone cũ
6. **Practical indicators bị cắt** — "Migr", "Sec", "Bench" bị truncate
7. **Warm-tone remnants** — dashboard.module.css vẫn còn `rgba(49,35,18,...)` sepia

## What Changes

Sửa toàn bộ frontend components và CSS để đồng bộ ngôn ngữ, bỏ elements thừa, khôi phục split view, và polish dark mode.

## Capabilities

### New Capabilities
- `label-localization`: Đồng bộ tất cả badge/tag labels sang tiếng Việt (trừ technical terms)
- `detail-split-restore`: Khôi phục split view 50/50 cho detail page (phân tích | bản gốc)
- `dark-mode-polish`: Fix dark mode contrast, warm-tone remnants, KPI card backgrounds

### Modified Capabilities
- `card-system`: Thêm thumbnail placeholder, fix tier label
- `detail-page`: Bỏ score bars sidebar, đổi layout về 50/50

## Impact

- **Files sửa**: `InsightCard.tsx`, `InsightDetail.tsx`, `Breadcrumb.tsx`, `global.css`, `dashboard.module.css`, `card.module.css`, `detail.module.css`
- **Không ảnh hưởng**: Backend, API, database, routing

## Non-goals
- Không thay đổi filter drawer logic
- Không thay đổi KPI summary component logic
- Không thêm features mới
