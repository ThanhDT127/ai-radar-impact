## 1. Playwright Feed Extraction

- [x] 1.1 Thêm tính năng `extract_from_feed` vào `PlaywrightConnector`.
- [x] 1.2 Triển khai hàm `_extract_feed_cards` để bóc tách trực tiếp văn bản từ các thẻ bài mà không cần click vào URL.
- [x] 1.3 Xử lý sinh Fake Hash ID (`#feed-hash`) để làm ID phân biệt cho các bài đăng không có direct link.

## 2. Anti-Bot & Rate Limiting

- [x] 2.1 Cấu hình `cookie_file` để truyền `storage_state` vào context của Playwright, giúp vượt qua màn hình đăng nhập (Login Wall) của LinkedIn/X.
- [x] 2.2 Bổ sung cơ chế `auto_scroll_count` (VD: lướt 2-3 lần) và `wait_for_timeout` sau mỗi lần lướt để mô phỏng hành vi người dùng thật.
- [x] 2.3 Thêm giới hạn `max_items` (cắt chuỗi ngay khi thu đủ số lượng bài để tránh spam query).

## 3. Database & Cấu hình Nguồn (Sources)

- [x] 3.1 Cập nhật bảng `sources` để hỗ trợ lưu trữ các config mới: `extract_from_feed: true`, `cookie_file: "path/to/cookies.json"`, `auto_scroll_count: 2`.
- [x] 3.2 Khởi tạo cấu hình cho tài khoản LinkedIn của OWASP / Anthropic / OpenAI để test luồng cào dữ liệu thực tế.
