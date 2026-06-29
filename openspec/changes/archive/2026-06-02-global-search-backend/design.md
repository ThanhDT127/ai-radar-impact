## Context

Hiện tại, trang Dashboard của AI Radar Impact có tính năng tìm kiếm nhưng hoạt động hoàn toàn ở Client-side. Khi người dùng nhập từ khóa tìm kiếm (lấy từ tham số URL `?search=...`), React UI sẽ thực hiện lọc cục bộ trên mảng `insights` thuộc trang hiện tại (tối đa 12 items). Điều này gây lỗi nghiêm trọng khi từ khóa tìm kiếm khớp với các insights ở các trang khác (ví dụ trang 2, trang 3) nhưng không hiển thị ở trang 1, dẫn đến trải nghiệm tìm kiếm không chính xác và thiếu sót dữ liệu.

## Goals / Non-Goals

**Goals:**
- Kết nối tính năng tìm kiếm từ Frontend xuống Database thông qua Backend API.
- Cải tiến endpoint `GET /api/v1/insights` nhận thêm tham số truy vấn `search` (tùy chọn).
- Cập nhật repository và SQLAlchemy query để thực hiện truy vấn tìm kiếm gần đúng (case-insensitive ILIKE) trên các cột `title`, `summary_short`, `summary_medium`, `signal`, và `so_what`.
- Thêm Search Input Box lên thanh Toolbar chính của frontend, hỗ trợ tự động đồng bộ hóa lên URL SearchParams và thực hiện debounce gọi API để tối ưu hóa hiệu suất.

**Non-Goals:**
- Không sử dụng Vector Search (pgvector) hay mô hình AI để tìm kiếm ngữ nghĩa ở Phase này.
- Không cấu hình cơ chế tìm kiếm toàn văn bản nâng cao (PostgreSQL Full-Text Search tsvector) để giữ thiết kế đơn giản theo quy tắc 1 developer.

## Decisions

### 1. Module bị ảnh hưởng
- **M5: Insight Repository:** Thêm logic tìm kiếm vào [insight_repo.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/repositories/insight_repo.py).
- **M6: Dashboard:** Sửa đổi [InsightList.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/pages/InsightList.tsx) để tích hợp Search Box và debounce API call.

### 2. Thiết kế Database & API Endpoint
- **Bảng DB bị ảnh hưởng:** Bảng `insights`. Không thêm cột mới, sử dụng các cột văn bản hiện có: `title`, `summary_short`, `summary_medium`, `signal`, `so_what`.
- **API Endpoint:** `GET /api/v1/insights`
  - Bổ sung query parameter: `search: Optional[str] = None`
  - Khi có `search`, SQLAlchemy query sẽ sử dụng điều kiện `or_` kết hợp `ilike` trên các trường văn bản của bảng `insights`.

### 3. Thiết kế Frontend & Debounce
- Thêm một ô nhập liệu `<input type="search" ... />` ngay trên thanh công cụ chính (Toolbar), bên cạnh dropdown sắp xếp và bộ lọc.
- Sử dụng hook debounce (hoặc setTimeout) khoảng `300ms` trước khi ghi từ khóa tìm kiếm vào URL SearchParams, kích hoạt TanStack Query fetch lại dữ liệu từ backend.
- Loại bỏ hoàn toàn logic lọc Client-side cũ trong `useMemo(() => filteredItems, ...)` để tránh trùng lặp bộ lọc.

## Risks / Trade-offs

- **Hiệu năng cơ sở dữ liệu:** Việc sử dụng `ILIKE '%search%'` có thể gây scan toàn bộ bảng (Seq Scan) nếu bảng `insights` phình to. Tuy nhiên, với quy mô dữ liệu Phase 1 (vài nghìn bản tin), truy vấn này vẫn chạy rất nhanh (< 10ms) và không cần thêm index phức tạp. Khi lên Phase 2 sẽ nâng cấp lên pgvector hoặc GIN index nếu cần thiết.
