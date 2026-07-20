## ADDED Requirements

### Requirement: CloakBrowser CDP routing
`PlaywrightConnector` MUST ưu tiên kết nối tới CloakBrowser qua CDP tại URL cấu hình `CLOAK_CDP_URL` (default `http://cloak:9222`); nếu kết nối thất bại hoặc URL rỗng, MUST fallback sang Chromium local và log rõ đường nào đang được dùng.

#### Scenario: Kết nối CloakBrowser thành công
- **WHEN** `CLOAK_CDP_URL` không rỗng và CDP endpoint phản hồi
- **THEN** connector dùng browser của CloakBrowser qua `connect_over_cdp`, log info xác nhận, và **không** override `user_agent` khi tạo context (để CloakBrowser tự quản fingerprint)

#### Scenario: Fallback Chromium local
- **WHEN** CDP endpoint không phản hồi hoặc `CLOAK_CDP_URL` rỗng
- **THEN** connector launch Chromium local headless với user-agent tĩnh như hiện tại, log warning nêu lý do fallback, và fetch tiếp tục bình thường

### Requirement: Nhịp cào trong phiên
Khi fetch nhiều bài trong cùng một phiên, connector MUST chờ một khoảng delay cấu hình được (kèm jitter ngẫu nhiên) giữa các lần load bài, để hành vi giống người dùng thật và tránh bị khóa tài khoản/chặn IP.

#### Scenario: Delay giữa các bài
- **WHEN** `_fetch_articles` xử lý danh sách nhiều URL
- **THEN** giữa hai lần `page.goto` liên tiếp có sleep = delay cơ sở + jitter ngẫu nhiên (default 2s + 0–2s), giá trị điều chỉnh được qua settings

### Requirement: Guard trùng nội dung trong batch
Trong một lần fetch, connector MUST bỏ qua entry có nội dung trích xuất trùng hệt (theo hash SHA256 của `raw_content`) với một entry đã lấy trước đó trong cùng batch, và log warning về số entry bị loại.

#### Scenario: Nhiều URL trả về cùng một trang shell
- **WHEN** N URL bài viết khác nhau cùng render ra một nội dung giống hệt nhau (ví dụ trang listing/anti-bot)
- **THEN** chỉ entry đầu tiên được giữ lại, N-1 entry sau bị skip, không tạo N documents trùng nội dung trong DB

## MODIFIED Requirements

### Requirement: PlaywrightConnector fetch
Hệ thống MUST có `PlaywrightConnector` kế thừa `BaseConnector`, dùng `sync_playwright()` để render trang JavaScript và trả về `list[ConnectorEntry]`.

#### Scenario: Fetch bài viết từ SPA
- **WHEN** `PlaywrightConnector.fetch(source)` được gọi với `source.source_type = "playwright"`
- **THEN** mở browser (CloakBrowser qua CDP hoặc Chromium local), điều hướng đến `source.feed_url`, extract danh sách link bài viết, fetch từng bài và trả về `list[ConnectorEntry]` với `source_url`, `title`, `raw_content`

#### Scenario: Context đóng sau khi fetch
- **WHEN** `fetch()` hoàn tất (thành công hoặc lỗi)
- **THEN** browser context MUST được đóng trong mọi nhánh (kể cả exception); với Chromium local, browser process MUST kết thúc không để zombie; với CDP, connector chỉ disconnect — MUST NOT kill browser dùng chung của CloakBrowser

### Requirement: Stealth mode
Khả năng né phát hiện bot được phân lớp: lớp chính là CloakBrowser (khi khả dụng), lớp fallback là init-script ẩn `navigator.webdriver` trên mỗi page. Connector MUST áp dụng init-script ẩn `navigator.webdriver` cho mọi page mới bất kể đường kết nối. (Thay thế yêu cầu cũ dùng thư viện `playwright-stealth` — không còn phản ánh thực tế.)

#### Scenario: Page mới được che webdriver flag
- **WHEN** `new_page()` được gọi (qua CDP hoặc local)
- **THEN** `page.add_init_script` ẩn `navigator.webdriver` MUST chạy trước `page.goto()`

#### Scenario: Anti-detection chính qua CloakBrowser
- **WHEN** connector đang dùng CloakBrowser qua CDP
- **THEN** fingerprint/anti-detection do CloakBrowser đảm nhiệm; connector MUST NOT ép các thuộc tính fingerprint tĩnh (user-agent, viewport cứng) đè lên context
