# Tasks: fix-insight-count-is-primary

> Nghiệm thu ở tầng API — không cần key Vertex, không cần crawl. Số liệu đối chiếu lấy từ DB hiện tại
> (đo 20/07/2026): KPI total 71→64, opportunities 64→57; 4 nguồn lệch (LinkedIn-OpenAI 5→2,
> HF Zhipu 3→1, HF Qwen 3→2, HF DeepSeek 2→1).

## 1. Rà soát

- [x] 1.1 Grep toàn bộ `func.count(Insight` + `count(*)` trên bảng `insights` trong `backend/app/repositories/` và `backend/app/services/`, liệt kê mọi chỗ đếm và đánh dấu chỗ nào thiếu `is_primary`. **DoD:** danh sách đầy đủ, xác nhận đúng 2 chỗ cần sửa (hoặc phát hiện thêm và bổ sung vào task 2).
- [x] 1.2 Ghi lại số liệu "trước khi sửa" từ API thật (`/api/v1/insights/stats` và `/api/v1/sources`) để đối chiếu sau. **DoD:** có snapshot số trước.

## 2. Sửa query

- [x] 2.1 `insight_repo.get_stats()`: thêm `Insight.is_primary == True` vào mệnh đề `where` (áp cho cả `total`, `critical_high`, `opportunities`). **DoD:** `/api/v1/insights/stats` trả `total=64`, `opportunities=57`, `critical_high=3`.
- [x] 2.2 `source_repo.list_with_insight_counts()`: thêm `Insight.is_primary == True` vào **điều kiện `outerjoin`** (không phải `where` — xem design D2). **DoD:** 4 nguồn lệch trả đúng số nhỏ; **và** tổng số nguồn trong response vẫn là 81 (không nguồn nào biến mất).

## 3. Kiểm chứng

- [x] 3.1 Nhất quán đếm–danh sách: với mỗi nguồn trong 4 nguồn lệch, so `insight_count` từ `/api/v1/sources` với `total` từ `/api/v1/insights?source_id=<id>`. **DoD:** khớp tuyệt đối cả 4.
- [x] 3.2 Kiểm scenario "nguồn chỉ toàn bản trùng": xác nhận nguồn dạng này trả `insight_count = 0` và vẫn có mặt trong response `/api/v1/sources`. **DoD:** đúng cả hai vế (nếu DB hiện không có nguồn nào như vậy thì dựng bằng cách set `is_primary=false` cho toàn bộ insight của 1 nguồn trong transaction rồi rollback).
- [x] 3.3 Kiểm không hồi quy `list_paginated` và `list_for_delivery` (vốn đã đúng): chạy `pytest backend/tests/` . **DoD:** toàn bộ test xanh.
- [x] 3.4 Kiểm UI: mở dashboard, bấm chip nguồn `LinkedIn - OpenAI`, đếm số thẻ hiện ra. **DoD:** số trên chip = số thẻ hiển thị.

## 4. Test hồi quy

- [x] 4.1 Test cho `get_stats()` trong `tests/test_insight_count_queries.py`. **Đổi cách làm:** repo không có hạ tầng test DB (không conftest/fixture; SQLite không thay được vì model dùng PostgreSQL `ARRAY`), nên test soi **SQL compile được** qua session giả thay vì dựng dữ liệu thật. **DoD ✅:** fail trên code cũ, pass trên code mới.
- [x] 4.2 Test cho `list_with_insight_counts()`: (a) có `is_primary` trong query; (b) `is_primary` nằm trong `JOIN ... ON` và query **không có `WHERE`** — khóa lại decision D2, bắt đúng kiểu hồi quy "chuyển điều kiện sang WHERE" vốn sẽ làm biến mất nguồn khỏi response. Nhánh dữ liệu thật đã nghiệm thu ở task 3.2 (transaction + rollback). **DoD ✅:** cả 3 test fail trên code cũ.

## 5. Tài liệu

- [x] 5.1 Ghi chú trong changelog/PR: KPI tụt 71→64 là **sửa lỗi đếm**, không phải mất dữ liệu. **DoD ✅:** `CHANGELOG_NOTE.md` trong change, có bảng trước/sau.
- [x] 5.2 Bổ sung gotcha vào `CLAUDE.md`: mọi query đếm insight hướng người dùng phải lọc `is_primary` — nêu rõ `list_with_insight_counts` phải đặt điều kiện ở `ON` của outer join chứ không phải `where`. **DoD:** người khác thêm endpoint đếm mới sẽ không lặp lỗi.
