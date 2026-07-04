## Why

Dữ liệu từ mạng xã hội chuyên gia (LinkedIn, X/Twitter, Reddit, HackerNews) chứa rất nhiều tín hiệu công nghệ sớm từ các tài khoản đầu ngành (như OpenAI, Anthropic) và các chuyên gia bảo mật. Tuy nhiên, các nền tảng này thường bảo vệ dữ liệu bằng cơ chế cuộn trang động (Infinite Scroll), yêu cầu đăng nhập (Cookies) và giới hạn số lượng request gắt gao (Rate-limiting/Bot blocking). Trình cào tin RSS truyền thống không thể lấy nội dung toàn vẹn từ các nguồn này, dẫn tới bỏ lỡ tín hiệu quan trọng.

## What Changes

- Mở rộng năng lực của `PlaywrightConnector` (thông qua `CloakBrowser`) để hỗ trợ chế độ trích xuất thẻ bài (Feed Card Extraction) thay vì chỉ bấm link truyền thống.
- Bổ sung cơ chế `auto_scroll_count` để tự động cuộn trang (simulate user scroll) thu thập bài viết cũ.
- Tích hợp `cookie_file` cho phép load phiên đăng nhập hợp lệ (tránh bị login wall của LinkedIn/X chặn).
- Triển khai thuật toán chống ban: giới hạn nghiêm ngặt `max_items` cào trong một lần chạy và giả lập hash ID.
- (Tùy chọn) Bổ sung Connector riêng biệt cho mạng xã hội nếu cần xử lý API public (như Reddit/HackerNews).

## Capabilities

### New Capabilities
- `social-media-ingestion`: Khả năng cuộn trang tự động, inject session cookies và trích xuất nội dung trực tiếp từ các Feed (Timeline) của mạng xã hội như LinkedIn, X thông qua CloakBrowser mà không bị khóa tài khoản.

### Modified Capabilities
- `playwright-spa-connector`: Nâng cấp connector để hỗ trợ cơ chế bóc tách thẻ bài trực tiếp (`extract_from_feed`) và giả lập hành vi người dùng (scroll).

## Impact

- **Mã nguồn bị ảnh hưởng:** `backend/app/connectors/playwright_connector.py`, cấu trúc của `Source` model (thêm cấu hình `auto_scroll_count`, `extract_from_feed`, `cookie_file`).
- **Hệ thống:** Mở rộng luồng Ingestion (M2) đón nhận các tin tức real-time từ MXH.
- **Dependencies:** Yêu cầu Playwright, CloakBrowser và cấu hình file lưu trữ phiên đăng nhập (.json cookies) hợp lệ.

## Non-goals

- Không hỗ trợ tự động giải mã CAPTCHA phức tạp (dùng cookie tĩnh đã xác thực trước).
- Không bình luận, like hay tương tác với bài viết MXH (Read-only).
- Không cào dữ liệu từ các tài khoản MXH bị khóa riêng tư (Private accounts).

## Phase & Dependencies
- **Phase áp dụng:** Phase 1 (Data Expansion)
- **Dependencies:** Cần container `cloakbrowser` hoạt động độc lập trong Docker Compose và người quản trị phải cấp sẵn file Cookies đăng nhập của nền tảng tương ứng.
