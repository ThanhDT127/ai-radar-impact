## Why

Dashboard có 3 lỗi UX/logic liên quan đến sort và filter: sort "Ảnh hưởng cao nhất" hiển thị kết quả sai vì badge và sort field không đồng nhất; các filter `urgency`, `momentum`, `vietnam_relevance` đã có đầy đủ ở API nhưng hoàn toàn ẩn trên UI; và role count chips tính từ page hiện tại (12 items) thay vì tổng dataset. Ba vấn đề này làm giảm đáng kể giá trị sử dụng của dashboard với 1,251 insights hiện có.

## What Changes

- **Fix sort "Ảnh hưởng cao nhất"**: Đổi sort option này từ `sort_by=impact_label` sang `sort_by=urgency` để đồng nhất với badge `UrgencyBadge` đang hiển thị trên card
- **Thêm filter urgency**: Chip filter cho 4 mức `critical / high / medium / low` — cho phép lọc 28 insights khẩn cấp nhất
- **Thêm filter momentum**: Chip filter cho `new / rising / mature` — cho phép lọc 118 tín hiệu mới và 190 rising
- **Thêm filter vietnam_relevance**: Chip filter `high / medium / low` — bề mặt 108 insights liên quan cao đến VN
- **Fix role count**: Bỏ count trên role chips hoặc chuyển sang dùng stats API thay vì đếm từ page hiện tại

## Capabilities

### New Capabilities
- `dashboard-actionable-filters`: Bộ filter UI cho urgency, momentum, vietnam_relevance trên dashboard insight list

### Modified Capabilities
- `insight-dashboard`: Sort "Ảnh hưởng cao nhất" đổi từ `impact_label` sang `urgency`; role chip count fix

## Impact

- **Frontend**: `SortDropdown.tsx` (đổi sort value), `InsightList.tsx` (thêm filter state + UI), `FilterChips.tsx` (reuse), `InsightList.tsx` (fix role count)
- **Backend**: Không thay đổi — API đã hỗ trợ đầy đủ `urgency`, `momentum`, `vietnam_relevance` filter params
- **API**: Không breaking — chỉ dùng thêm params đã có sẵn

## Non-goals

- Không thêm filter `topics` hay `event_type` (scope riêng)
- Không thay đổi layout card hay badge rendering
- Không thêm persisted filter state (URL params) — đơn giản hóa scope
- Không thêm filter tổng hợp (AND/OR logic) — mặc định AND đã đủ
