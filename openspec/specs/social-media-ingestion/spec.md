## ADDED Requirements

### Requirement: Feed Card Extraction
Hệ thống Ingestion (M2) phải hỗ trợ chế độ trích xuất nội dung trực tiếp từ các thẻ bài (Feed Card) trên mạng xã hội mà không cần click vào link chi tiết.

#### Scenario: Cào nội dung từ trang Feed của LinkedIn
- **WHEN** source_type là web và config có `extract_from_feed` = true
- **THEN** PlaywrightConnector bỏ qua bước quét `<a>` links, thay vào đó quét các thẻ DOM theo `link_selector` (card_selector) và lấy `inner_text()` của từng thẻ, sau đó băm Hash 50 ký tự đầu tiên để làm ID giả.

### Requirement: Auto-Scroll Limit
Hệ thống phải có khả năng cuộn trang (simulate human scroll) một số lần giới hạn để load bài đăng cũ trên MXH mà không bị khóa tài khoản do hành vi spam.

#### Scenario: Vượt qua infinite scroll an toàn
- **WHEN** config của Source quy định `auto_scroll_count` = N
- **THEN** PlaywrightConnector thực hiện lệnh `window.scrollTo` xuống cuối trang N lần, mỗi lần chờ 2 giây để DOM render, trước khi tiến hành bóc tách thẻ bài.

### Requirement: Session Cookies Injection
Hệ thống phải hỗ trợ load trạng thái đăng nhập hợp lệ để vượt rào truy cập ẩn danh (Login Wall) của LinkedIn/X.

#### Scenario: Cào trang yêu cầu đăng nhập
- **WHEN** config của Source chứa đường dẫn hợp lệ trong `cookie_file`
- **THEN** Playwright tạo Context trình duyệt với `storage_state` nạp từ file JSON đó, cho phép truy cập Feed dưới tư cách User hợp lệ đã login trước đó.
