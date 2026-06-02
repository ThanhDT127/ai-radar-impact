## Why

Dashboard hiện chia 3 tabs (Tổng quan / Theo nguồn / Theo vai trò) nhưng cả 3 tabs đều hiện cùng 1 loại data — insight cards. Khác biệt duy nhất là tab "Theo nguồn" thêm source filter chips và tab "Theo vai trò" thêm role filter chips. Điều này gây nhầm lẫn vì user phải chuyển tab mới thấy filter cần dùng, và mỗi lần chuyển tab thì reset hết filters đã chọn.

## What Changes

1. **Xóa TabBar** — gộp 3 tabs thành 1 unified view
2. **Gộp tất cả filters vào 1 panel duy nhất**: urgency, momentum, vietnam, tier, sources, roles — luôn available
3. **Filter panel luôn visible** (không cần toggle button) — layout compact, scrollable horizontal chips
4. Source filter + role filter chuyển từ tab-conditional → luôn hiện trong filter panel
5. Thêm **search box** vào toolbar để tìm nhanh theo tiêu đề

## Capabilities

### New Capabilities
_(Không có capability mới — gộp UI hiện có)_

### Modified Capabilities
_(Không thay đổi requirements — cùng data, cùng filters, chỉ gộp layout)_

## Impact

**Frontend files:**
- `pages/InsightList.tsx` — MODIFY: xóa tab logic, gộp filters, thêm search
- `components/TabBar.tsx` — DELETE (hoặc stop using)
- `styles/dashboard.module.css` — MODIFY: xóa tab CSS, thêm unified filter bar CSS

**Backend:** Không thay đổi

**Non-goals:**
- Không thêm filter mới (topic filter, date range — change riêng nếu cần)
- Không thay đổi InsightCard layout (change riêng: insight-card-redesign)
- Không sửa API endpoint

**Phase:** Phase 1
