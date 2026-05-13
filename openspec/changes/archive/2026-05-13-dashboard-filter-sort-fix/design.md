## Context

Dashboard hiện tại (M6) có 3 vấn đề logic:

1. **Sort mismatch**: `SortDropdown` gửi `sort_by=impact_label` cho option "Ảnh hưởng cao nhất", nhưng `InsightCard` hiển thị `UrgencyBadge` (field `urgency`) — không phải `ImpactBadge`. Người dùng thấy badge urgency nhưng kết quả sort theo impact_label → trông như sắp xếp sai.

2. **Filter ẩn**: API `/api/v1/insights` đã nhận `urgency`, `momentum`, `vietnam_relevance` params từ trước nhưng InsightList không expose UI controls nào cho 3 filter này. 1,251 insights với metadata đầy đủ nhưng người dùng không lọc được.

3. **Role count sai**: Role filter chips tính count từ `overviewQuery.data?.items` (tối đa 12 items/page) thay vì total dataset → số hiển thị vô nghĩa.

Không có thay đổi backend, không có DB migration. Toàn bộ là frontend-only.

## Goals / Non-Goals

**Goals:**
- Sort "Ảnh hưởng cao nhất" đồng nhất với badge hiển thị (urgency)
- 3 bộ filter mới (urgency, momentum, vietnam_relevance) hoạt động với API hiện có
- Role count không hiển thị số sai

**Non-Goals:**
- Không thay đổi backend API hay DB
- Không persist filter state lên URL
- Không thêm filter topics/event_type/nature
- Không redesign layout

## Decisions

### 1. Đổi sort value từ `impact_label` → `urgency`

`SortDropdown` option "Ảnh hưởng cao nhất": đổi `value: 'impact_label'` thành `value: 'urgency'`. Label giữ nguyên. API đã nhận `sort_by=urgency` và có `_URGENCY_ORDER` CASE expression đúng (critical→high→medium→low). Không cần thêm `urgency` vào `InsightSort` type vì đã có trong API schema.

**Thay thế đã xét**: Đổi badge hiển thị thành `ImpactBadge` khi sort theo impact_label. Bác bỏ vì `urgency` thực chất hữu ích hơn cho người dùng (time-sensitive), còn `impact_label` chỉ là classification tĩnh theo event_type.

### 2. Filter UI: reuse `FilterChips` trong collapsible toolbar

Thêm 3 `FilterChips` group cho urgency/momentum/vietnam_relevance ngay dưới SortDropdown, hiển thị luôn (không phụ thuộc tab). Reuse component `FilterChips` hiện có.

Labels:
```
urgency:           critical→"Khẩn cấp" | high→"Cao" | medium→"Trung bình" | low→"Thấp"
momentum:          new→"Mới" | rising→"Đang nổi" | mature→"Ổn định"
vietnam_relevance: high→"Liên quan cao" | medium→"Liên quan vừa" | low→"Thấp"
```

State: 3 `useState<string[]>` mới trong InsightList, reset khi tab thay đổi. Truyền vào `fetchInsights` params.

**Thay thế đã xét**: Dropdown filter thay vì chips. Bác bỏ vì chips cho phép multi-select trực quan hơn, và `FilterChips` component đã có sẵn.

### 3. Role count: bỏ count, không hiển thị số

Đơn giản nhất: truyền `count: undefined` cho tất cả role chips thay vì tính từ page. `FilterChips` đã handle `count: undefined` (không render số). Không gọi thêm API.

**Thay thế đã xét**: Gọi `/api/v1/insights/stats` để lấy role breakdown. Bác bỏ vì stats API hiện không có breakdown theo role, cần thêm endpoint mới — over-engineering cho fix nhỏ.

## Risks / Trade-offs

- **Filter mặc định không active**: 3 filter mới mặc định là [] (không lọc) → không break UX hiện tại.
- **Filter combinations**: urgency + momentum + vietnam_relevance + role + source có thể trả về 0 kết quả. `InsightList` đã có empty state handler.
- **Performance**: Không thêm query — `fetchInsights` thêm params vào request hiện có; backend đã có WHERE clause cho các filter này.

## Migration Plan

Không có migration. Thay đổi thuần frontend, deploy không cần downtime hay DB change.
