## Why

4 ô KPI trên đầu dashboard (Tổng bản tin, Mức ảnh hưởng cao, Cơ hội, Nguồn hoạt động) hiện chỉ hiện con số trơ trụi. User nhìn vào "102" không biết đây là gì — critical alerts? bài nên đọc? Không có chú thích, không có xu hướng, không có ngữ cảnh.

Dependency: `tooltip-annotation-system` (dùng Tooltip cho icon ⓘ).

## What Changes

1. Thêm **subtitle** mô tả dưới mỗi số (luôn hiện, không cần hover)
2. Thêm **tooltip icon ⓘ** bên cạnh label → hover hiện giải thích chi tiết
3. Đổi tên label cho rõ nghĩa hơn ("Mức ảnh hưởng cao" → "Ảnh hưởng cao", "Cơ hội" → "Cơ hội hành động")
4. Thêm **semantic color** cho số (đỏ nếu critical_high tăng, xanh cho opportunities)
5. **Không thêm delta/sparkline** ở change này (cần backend endpoint mới, để change riêng nếu cần)

## Capabilities

### New Capabilities
_(Không có capability mới — nâng cấp UI component hiện có)_

### Modified Capabilities
_(Không thay đổi requirements ở spec level — chỉ cải thiện UX presentation)_

## Impact

**Frontend:**
- `components/KPISummary.tsx` — MODIFY: thêm subtitles, tooltip, semantic colors
- `styles/dashboard.module.css` — MODIFY: CSS cho subtitle, tooltip icon, color coding

**Backend:** Không thay đổi

**Non-goals:**
- Không thêm delta comparison (cần backend endpoint stats/delta)
- Không thêm sparkline charts (over-engineering cho Phase 1)
- Không thay đổi layout 4 cột

**Phase:** Phase 1
**Dependency:** `tooltip-annotation-system`
