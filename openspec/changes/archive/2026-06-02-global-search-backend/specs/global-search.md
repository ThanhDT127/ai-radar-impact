## ADDED Requirements

### Requirement: search-insights-backend
Endpoint GET `/api/v1/insights` phải hỗ trợ tham số truy vấn `search` để tìm kiếm các bản tin khớp với từ khóa từ database.

#### Scenario: search-with-keyword
- **WHEN** Gửi yêu cầu GET `/api/v1/insights?search=npm`
- **THEN** Backend trả về danh sách các insights chứa từ khóa "npm" trong tiêu đề (`title`) hoặc nội dung (`summary_short`, `summary_medium`, `signal`, `so_what`).

#### Scenario: search-with-empty-results
- **WHEN** Gửi yêu cầu GET `/api/v1/insights?search=nonexistentkeyword123`
- **THEN** Backend trả về danh sách rỗng (`items: []`) với tổng số lượng bằng 0 (`total: 0`).

### Requirement: search-insights-frontend
Giao diện Dashboard chính phải hiển thị ô nhập tìm kiếm toàn cục trên Toolbar, hỗ trợ gõ từ khóa tìm kiếm và tự động cập nhật URL.

#### Scenario: enter-search-query
- **WHEN** Người dùng nhập "Gemini" vào ô tìm kiếm trên Toolbar
- **THEN** Sau 300ms, URL được cập nhật thành `/?search=Gemini` và danh sách bài viết được làm mới tương ứng với kết quả từ Backend API.

#### Scenario: clear-search-query
- **WHEN** Người dùng xóa nội dung trong ô tìm kiếm hoặc click vào dấu "×" trên filter chip tìm kiếm
- **THEN** URL xóa bỏ tham số `search` và danh sách bài viết được khôi phục về trạng thái không lọc.
