## ADDED Requirements

### Requirement: PlaywrightConnector fetch
Hệ thống MUST có `PlaywrightConnector` kế thừa `BaseConnector`, dùng `sync_playwright()` để render trang JavaScript và trả về `list[ConnectorEntry]`.

#### Scenario: Fetch bài viết từ SPA
- **WHEN** `PlaywrightConnector.fetch(source)` được gọi với `source.source_type = "playwright"`
- **THEN** mở headless Chromium, điều hướng đến `source.feed_url`, extract danh sách link bài viết, fetch từng bài và trả về `list[ConnectorEntry]` với `source_url`, `title`, `raw_content`

#### Scenario: Browser đóng sau khi fetch
- **WHEN** `fetch()` hoàn tất (thành công hoặc lỗi)
- **THEN** Chromium browser MUST được đóng, không để process zombie

### Requirement: Config-driven behavior
`PlaywrightConnector` MUST đọc các tham số từ `source.config` để điều chỉnh hành vi per-source mà không cần sửa code.

#### Scenario: link_selector lọc link
- **WHEN** `source.config["link_selector"]` được cấu hình (vd: `"article a"`)
- **THEN** chỉ extract links khớp với CSS selector đó trên trang listing

#### Scenario: link_pattern lọc link theo URL
- **WHEN** `source.config["link_pattern"]` được cấu hình (vd: `"/tin-tuc/[^/]+"`)
- **THEN** chỉ lấy links mà URL match regex pattern, bỏ qua links ngoài pattern

#### Scenario: max_items giới hạn số bài
- **WHEN** `source.config["max_items"]` được đặt (default `10`)
- **THEN** connector MUST dừng sau khi đủ số bài, không fetch thêm

#### Scenario: wait_for chờ selector
- **WHEN** `source.config["wait_for"]` là CSS selector không rỗng
- **THEN** sau khi goto(), connector MUST gọi `page.wait_for_selector(wait_for)` trước khi extract links

### Requirement: Stealth mode
`PlaywrightConnector` MUST áp dụng `playwright-stealth` trên mỗi page mới để bypass fingerprint detection cơ bản.

#### Scenario: Stealth được áp dụng
- **WHEN** `new_page()` được gọi
- **THEN** `stealth_sync(page)` MUST được gọi ngay trước `page.goto()`

### Requirement: Lỗi per-bài không làm hỏng batch
Nếu một bài viết không fetch được, `PlaywrightConnector` MUST log warning và tiếp tục các bài còn lại.

#### Scenario: Một bài lỗi
- **WHEN** `page.goto(article_url)` hoặc trafilatura extract thất bại cho một bài
- **THEN** log warning với URL và error, skip bài đó, tiếp tục fetch bài tiếp theo

#### Scenario: Toàn bộ listing page lỗi
- **WHEN** goto(source.feed_url) thất bại hoặc timeout
- **THEN** log error và trả về `[]`, không raise exception

### Requirement: Tái dụng trafilatura để extract nội dung
Sau khi Playwright render HTML, `PlaywrightConnector` MUST dùng `trafilatura.extract()` để lấy nội dung bài viết — không tự parse HTML.

#### Scenario: Extract nội dung thành công
- **WHEN** `page.content()` trả về HTML đầy đủ của bài viết
- **THEN** `trafilatura.extract(html)` được gọi và kết quả được đặt vào `ConnectorEntry.raw_content`

#### Scenario: trafilatura không extract được
- **WHEN** `trafilatura.extract()` trả về `None` hoặc chuỗi rỗng
- **THEN** bài viết đó bị skip (không tạo `ConnectorEntry`)
