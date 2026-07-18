# telegram-bot-transport

## ADDED Requirements

### Requirement: Channel adapter interface trung lập kênh
Hệ thống SHALL định nghĩa interface `ChannelAdapter` (gửi `DeliveryMessage` trung lập kênh tới `recipient_ref`) và `TelegramAdapter` là implementation đầu tiên. Delivery engine SHALL chỉ phụ thuộc interface, không phụ thuộc chi tiết Telegram.

#### Scenario: Thêm kênh mới không sửa engine
- **WHEN** một adapter mới (vd. Zalo) được đăng ký với cùng interface
- **THEN** delivery engine gửi được qua kênh mới mà không thay đổi code engine

### Requirement: Nhận update qua long-polling, không cần webhook
Bot SHALL nhận update từ Telegram bằng long-polling (`getUpdates`) chạy như worker trong môi trường docker-compose local, không yêu cầu webhook/domain public. Worker SHALL tự khởi động lại với backoff khi lỗi và ghi log heartbeat.

#### Scenario: Chạy hoàn toàn local
- **WHEN** hệ thống khởi động bằng docker-compose trên máy dev không có IP public
- **THEN** bot nhận và phản hồi tin nhắn bình thường

#### Scenario: Worker gặp lỗi mạng
- **WHEN** long-polling gặp lỗi kết nối
- **THEN** worker retry với backoff và tiếp tục nhận update sau khi mạng phục hồi, không cần restart thủ công

### Requirement: Bật/tắt bằng cấu hình
Bot worker SHALL chỉ khởi động khi có `TELEGRAM_BOT_TOKEN` và `DELIVERY_ENABLED=true`; khi thiếu, phần còn lại của hệ thống SHALL hoạt động bình thường. Token SHALL đọc từ env, không hardcode trong repo.

#### Scenario: Thiếu token
- **WHEN** backend khởi động không có `TELEGRAM_BOT_TOKEN`
- **THEN** bot worker không start, API/pipeline chạy bình thường, log ghi rõ delivery bị tắt

### Requirement: Routing update cho các consumer
Transport SHALL phân loại update và route: lệnh (`/start`, `/subscribe`, `/unsubscribe`, `/status`, `/reset`) → subscription/chat handler tương ứng; callback nút inline `ask:<insight_id>` → chat handler; text tự do → chat handler. Khi chat handler (change `chatbot-qa`) chưa được triển khai, callback `ask:`, text tự do và lệnh `/reset` SHALL nhận phản hồi tạm lịch sự kèm link dashboard.

#### Scenario: Chat handler chưa có
- **WHEN** người dùng bấm nút "Hỏi về tin này" khi chatbot chưa được triển khai
- **THEN** bot trả lời rằng tính năng hỏi đáp sắp ra mắt kèm link insight trên dashboard

### Requirement: Gửi an toàn trong giới hạn Telegram
Adapter SHALL render bằng HTML parse mode, escape nội dung động, và tự chia/cắt message để không vượt giới hạn 4096 ký tự của Telegram.

#### Scenario: Title chứa ký tự đặc biệt
- **WHEN** insight có title chứa `<`, `&` hoặc ký tự đặc biệt khác
- **THEN** message gửi thành công và hiển thị đúng nội dung

#### Scenario: Digest dài
- **WHEN** nội dung digest render vượt 4096 ký tự
- **THEN** adapter chia thành nhiều message hợp lệ, không lỗi gửi
