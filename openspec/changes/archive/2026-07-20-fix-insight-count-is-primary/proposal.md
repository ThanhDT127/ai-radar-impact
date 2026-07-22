## Why

Các con số đếm insight trên dashboard **không khớp với thứ người dùng bấm vào xem được**. Danh sách
(`list_paginated`) lọc `is_primary = True` để mỗi cụm trùng ngữ nghĩa chỉ hiện một đại diện, nhưng
KPI cards (`get_stats`) và bộ đếm nguồn (`list_with_insight_counts`) đếm **mọi** insight `published`,
kể cả bản trùng đã bị `DeduplicationEngine` gộp và ẩn đi. Requirement hiện có trong `semantic-dedup`
("Dashboard chỉ hiện primary") chỉ ràng buộc endpoint danh sách, nên hai chỗ đếm này trôi tự do.

Lệch đo được trên DB hiện tại (20/07/2026):

| Chỗ hiển thị | Đang hiện | Xem được thật |
|---|---|---|
| KPI "Tổng insight" | 71 | 64 |
| KPI "Cơ hội" | 64 | 57 |
| KPI "Nghiêm trọng/Cao" | 3 | 3 |
| Chip nguồn `LinkedIn - OpenAI` | 5 | 2 |
| Chip nguồn `HF Zhipu (GLM)` | 3 | 1 |
| Chip nguồn `HF Qwen` | 3 | 2 |
| Chip nguồn `HF DeepSeek` | 2 | 1 |

Người dùng bấm vào chip báo 5 bài thì chỉ thấy 2 — mất niềm tin vào toàn bộ số liệu trên trang. Đây
là lỗi có sẵn (3 nguồn HuggingFace lệch từ trước), không phải hệ quả của thay đổi gần đây; nó chỉ vừa
lộ rõ khi một nguồn sinh nhiều bản trùng cùng lúc.

## What Changes

- `get_stats()` lọc thêm `is_primary = True` cho cả 3 con số (`total`, `critical_high`,
  `opportunities`) → KPI phản ánh đúng số thẻ người dùng xem được.
- `list_with_insight_counts()` đưa `Insight.is_primary == True` vào điều kiện outer join → chip nguồn
  đếm theo cụm, khớp với kết quả khi bấm lọc theo nguồn đó.
- Bổ sung requirement trong `semantic-dedup`: **mọi** con số đếm insight hướng người dùng phải đếm
  theo đại diện cụm, không đếm bản trùng. Ràng buộc này áp cho cả các endpoint đếm sau này, để lỗi
  không tái diễn ở chỗ đếm mới.
- Không đụng `DeduplicationEngine`, không đụng cách gom cụm, không đổi dữ liệu — chỉ sửa cách đếm.
- Không đụng `list_for_delivery` (đã lọc `is_primary` đúng) và `list_paginated` (đã đúng).

## Capabilities

### New Capabilities
_(không có — chỉ siết requirement của capability hiện hữu)_

### Modified Capabilities
- `semantic-dedup`: mở rộng requirement "Dashboard chỉ hiện primary" từ chỗ chỉ ràng buộc endpoint
  danh sách sang ràng buộc **mọi bộ đếm hướng người dùng** (KPI stats, đếm insight theo nguồn), để
  con số và danh sách luôn nhất quán.

## Impact

- **Code**: `backend/app/repositories/insight_repo.py` (`get_stats`),
  `backend/app/repositories/source_repo.py` (`list_with_insight_counts`).
- **API**: `GET /api/v1/insights/stats` và `GET /api/v1/sources` trả số nhỏ hơn hiện tại (đúng hơn).
  Không đổi shape response — thuần thay đổi giá trị, frontend không cần sửa.
- **Frontend**: không sửa. `InsightList.tsx` phân nhánh `insight_count > 0` để quyết định nguồn nào
  thành chip lọc; sau fix, nguồn mà toàn bộ insight đều là bản trùng sẽ đúng đắn rơi xuống dòng
  "chưa có insight".
- **Dữ liệu**: không migration, không backfill.
- **Rủi ro**: thấp. Con số KPI sẽ giảm (71→64) — cần nói rõ trong changelog để người dùng không tưởng
  là mất dữ liệu.
