## Why

Hiện tại, thanh tìm kiếm trên trang Dashboard của AI Radar Impact chỉ lọc dữ liệu cục bộ trên Client-side đối với trang hiện tại (tối đa 12 bài viết đang hiển thị). Điều này khiến người dùng không thể tìm thấy các bài viết khớp từ khóa nằm ở các trang tiếp theo. Ngoài ra, giao diện chính thiếu ô nhập tìm kiếm toàn cục, buộc người dùng phải click vào các nhãn danh mục để tìm kiếm gián tiếp. Thay đổi này nhằm sửa lỗi lọc tìm kiếm và tích hợp ô tìm kiếm toàn cục kết nối trực tiếp với Backend API.

## What Changes

- **Backend API (`/api/v1/insights`):** Hỗ trợ nhận tham số truy vấn `search` (chuỗi ký tự tìm kiếm) để thực hiện tìm kiếm full-text search hoặc LIKE trên tiêu đề, tóm tắt và nội dung của insights từ database.
- **Frontend Dashboard:**
  - Bổ sung ô nhập liệu tìm kiếm (Search Input Box) nằm trên thanh công cụ chính (Toolbar), hiển thị trực quan và hỗ trợ debounce input để tối ưu hóa tần suất gọi API.
  - Sửa đổi cơ chế lọc Client-side hiện tại thành gửi yêu cầu tìm kiếm trực tiếp lên Backend khi người dùng gõ từ khóa hoặc click vào các Topic/Role tag.

### Non-goals
- Không triển khai tìm kiếm ngữ nghĩa (Semantic Search) bằng Vector Embedding hay pgvector (sẽ thuộc Phase 2).
- Không thêm tính năng lưu lịch sử tìm kiếm của người dùng hay gợi ý từ khóa thông minh (Auto-suggest).

### Phase áp dụng: Phase 1 (MVP)

### Dependencies
- Phụ thuộc vào Module M5 (Insight Repository) và M6 (Dashboard).

## Capabilities

### New Capabilities
- Không có.

### Modified Capabilities
- `insight-api`: Thêm tham số `search` trong endpoint GET `/api/v1/insights` và thực hiện tìm kiếm ở tầng Database.
- `insight-dashboard`: Thay thế ô tìm kiếm Client-side hiện tại bằng ô tìm kiếm toàn cục tích hợp Backend API trên Toolbar.

## Impact

- **Backend:** File [insights.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/routes/insights.py) và [insight_repo.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/repositories/insight_repo.py).
- **Frontend:** File [InsightList.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/pages/InsightList.tsx) và [insights.ts](file:///d:/Works/AI%20Radar%20Impact/frontend/src/api/insights.ts).
- **Database:** Thực hiện truy vấn SELECT ... WHERE title ILIKE %search% OR summary_short ILIKE %search% ...
