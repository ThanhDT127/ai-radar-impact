## ADDED Requirements

### Requirement: Extract Full Text using Trafilatura
Hệ thống phải có khả năng bóc tách văn bản gốc từ mã nguồn HTML của trang web thay vì chỉ lấy tóm tắt RSS.

#### Scenario: RSS feed content is too short
- **WHEN** nội dung bài viết lấy từ RSS feed có độ dài dưới 500 ký tự.
- **THEN** hệ thống sẽ khởi tạo luồng kết nối tới URL gốc qua Playwright, lấy HTML và sử dụng Trafilatura để xuất ra văn bản thuần tuý (text-only).

### Requirement: Bypass Anti-Bot mechanisms
Hệ thống phải vượt qua được các trang web cấm crawler tự động bằng cách sử dụng trình duyệt thật.

#### Scenario: Connecting to anti-bot protected site
- **WHEN** hệ thống cần tải trang web từ GitHub, HuggingFace.
- **THEN** hệ thống sử dụng kết nối CDP tới `http://cloak:9222` để chạy Headless Chromium, chèn script xóa flag `navigator.webdriver`, và chờ DOMContentLoaded trước khi lấy HTML.
