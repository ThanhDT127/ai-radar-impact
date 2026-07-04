## 1. Backend Implementation

- [x] 1.1 Thêm tham số `search` kiểu `Optional[str]` vào route handler `get_insights` trong [insights.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/routes/insights.py).
- [x] 1.2 Cập nhật phương thức `get_insights` trong [insight_repo.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/repositories/insight_repo.py) để nhận tham số `search`.
- [x] 1.3 Cập nhật truy vấn SQLAlchemy trong [insight_repo.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/repositories/insight_repo.py) sử dụng `or_` và `ilike` để lọc theo tiêu đề (`title`), tóm tắt (`summary_short`, `summary_medium`), tín hiệu (`signal`), và ý nghĩa (`so_what`).

## 2. Frontend API & Layout

- [x] 2.1 Cập nhật hàm `fetchInsights` trong [insights.ts](file:///d:/Works/AI%20Radar%20Impact/frontend/src/api/insights.ts) để truyền tham số `search` lên Backend API.
- [x] 2.2 Thêm ô nhập liệu tìm kiếm `<input type="search" ... />` vào Toolbar trong [InsightList.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/pages/InsightList.tsx).
- [x] 2.3 Áp dụng CSS Modules styling cho ô tìm kiếm trong [dashboard.module.css](file:///d:/Works/AI%20Radar%20Impact/frontend/src/styles/dashboard.module.css).

## 3. Interaction & Sync

- [x] 3.1 Cấu hình debounce (300ms) khi người dùng gõ tìm kiếm để tránh gọi API liên tục.
- [x] 3.2 Đồng bộ trạng thái tìm kiếm với URL SearchParams (`?search=...`) khi kết thúc debounce.
- [x] 3.3 Loại bỏ logic lọc client-side cũ (`useMemo` trên `filteredItems`) và thay thế bằng việc hiển thị trực tiếp dữ liệu từ Query.

## 4. Verification

- [x] 4.1 Kiểm tra gọi API trực tiếp với tham số `search` hoạt động chính xác.
- [x] 4.2 Kiểm tra ô tìm kiếm hiển thị đúng và đồng bộ trạng thái lên URL trên trình duyệt.
- [x] 4.3 Chạy thử nghiệm tự động bằng Playwright để xác nhận các Scenario trong đặc tả spec đều đạt.
