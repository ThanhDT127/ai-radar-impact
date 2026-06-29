## ADDED Requirements

### Requirement: Điều khiển bố cục đọc linh hoạt (Fluid Split-View Controls)

Trang chi tiết Insight MUST tích hợp bộ điều khiển cho phép người dùng chuyển đổi giữa 3 chế độ đọc: Split View (50/50), Focus AI (80/20), Focus Original (20/80) và tự động lưu lựa chọn này vào bộ nhớ trình duyệt (`localStorage`).

#### Scenario: Giao diện bộ điều khiển chế độ đọc
- **WHEN** người dùng mở trang chi tiết Insight
- **THEN** trang chi tiết MUST hiển thị một toolbar nhỏ chứa 3 nút chuyển chế độ ở đầu trang: "Đọc song song" (Split), "Tập trung AI" (Focus AI), và "Tập trung Nguồn" (Focus Original)
- **AND** chế độ được chọn mặc định từ đầu SHALL là chế độ lưu trong `localStorage` (hoặc fallback về 'split' nếu chưa lưu)

#### Scenario: Chuyển sang chế độ Focus AI (Tập trung phân tích)
- **WHEN** người dùng click vào nút "Tập trung AI"
- **THEN** cột phân tích AI bên trái MUST mở rộng chiếm 80% chiều rộng màn hình
- **AND** cột bài gốc bên phải MUST thu hẹp còn 20%
- **AND** cột bài gốc bên phải MUST ẩn nội dung iframe đi, thay thế bằng tiêu đề bài gốc và nút bấm mở rộng nhanh "Đọc song song ◀"

#### Scenario: Chuyển sang chế độ Focus Original (Tập trung bài gốc)
- **WHEN** người dùng click vào nút "Tập trung Nguồn"
- **THEN** cột bài gốc bên phải MUST mở rộng chiếm 80% chiều rộng màn hình
- **AND** cột phân tích AI bên trái MUST thu hẹp còn 20%
- **AND** cột phân tích AI bên trái MUST ẩn các mục văn bản dài (bullets, khuyến nghị, rủi ro) và chỉ giữ lại tiêu đề kèm nút bấm mở rộng "Đọc song song ▶"

#### Scenario: Hiệu ứng chuyển cảnh mượt mà
- **WHEN** người dùng chuyển đổi giữa bất kỳ chế độ nào trong 3 chế độ đọc
- **THEN** kích thước các cột MUST thay đổi thông qua một hiệu ứng chuyển cảnh mượt mà bằng CSS (transition) với thời gian chuyển tiếp từ 0.2s đến 0.4s
