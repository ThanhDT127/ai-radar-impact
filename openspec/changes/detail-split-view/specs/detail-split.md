## ADDED Requirements

### Requirement: Layout chia đôi trang chi tiết (Detail Split-View)

Trang chi tiết Insight (`InsightDetail`) MUST hiển thị dạng split-view chia đôi tỉ lệ 50/50 trên màn hình lớn (>= 1024px): panel bên trái hiển thị nội dung phân tích tóm tắt bằng tiếng Việt, panel bên phải hiển thị bài viết gốc bằng tiếng Anh.

#### Scenario: Hiển thị trên màn hình Desktop
- **WHEN** người dùng truy cập trang chi tiết với chiều rộng màn hình >= 1024px
- **THEN** trang chi tiết MUST hiển thị dạng split-view chia đôi 50/50
- **THEN** panel bên trái hiển thị đầy đủ thông tin phân tích của AI (title, tags, 5 bullets, khuyến nghị, rủi ro, scoring)
- **THEN** panel bên phải hiển thị bài viết gốc nhúng trong iframe thông qua `source_url`

#### Scenario: Tải thành công bài viết gốc trong iframe
- **WHEN** iframe tải thành công nội dung từ `source_url`
- **THEN** panel bên phải MUST hiển thị nội dung trang web gốc một cách mượt mà và trực quan

#### Scenario: Iframe bị chặn hoặc lỗi tải trang
- **WHEN** iframe không thể hiển thị nội dung (do lỗi mạng hoặc do chính sách bảo mật X-Frame-Options)
- **THEN** panel bên phải SHALL hiển thị một giao diện fallback thay thế
- **THEN** giao diện fallback MUST bao gồm tiêu đề bài viết gốc và một nút bấm nổi bật "Mở bài gốc trong tab mới"

#### Scenario: Hiển thị trên thiết bị di động
- **WHEN** người dùng truy cập trang chi tiết trên thiết bị di động hoặc máy tính bảng có màn hình < 1024px
- **THEN** bố cục split-view MUST tự động chuyển sang dạng xếp chồng dọc (stack vertical)
- **THEN** panel phân tích AI hiển thị ở phía trên và panel bài viết gốc hiển thị ở phía dưới

#### Scenario: Hiển thị verification badge của AI
- **WHEN** panel phân tích AI tải thành công
- **THEN** panel trái MUST hiển thị verification badge "🤖 Phân tích bởi Gemini AI"
- **THEN** badge này SHALL hiển thị rõ ràng độ tin cậy (confidence) của mô hình AI dưới dạng phần trăm (ví dụ: "Confidence: 85%")
