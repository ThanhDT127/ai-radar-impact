# chat-telegram-surface

## ADDED Requirements

### Requirement: Hỏi đáp toàn cục qua tin nhắn Telegram
Bot SHALL coi tin nhắn văn bản tự do (không phải lệnh `/...`) từ một chat đã `/start` là câu hỏi chế độ toàn cục, gọi chat service và trả lời kèm citation dạng link Telegram.

#### Scenario: Nhắn câu hỏi cho bot
- **WHEN** người dùng đã `/start` nhắn "tuần này có gì đáng chú ý cho Data/AI?"
- **THEN** bot trả lời bằng tiếng Việt kèm link các insight nguồn

#### Scenario: Chat chưa /start
- **WHEN** hệ thống nhận update từ chat chưa từng `/start`
- **THEN** bot gửi hướng dẫn bắt đầu, không gọi chat service

### Requirement: Phiên hỏi theo insight qua nút inline
Khi người dùng bấm nút inline "Hỏi về tin này" trên một tin push, bot SHALL đặt context phiên của chat đó về insight tương ứng (lưu `chat_sessions.context_insight_id`); các câu hỏi sau đó SHALL chạy chế độ per-insight cho đến khi người dùng thoát context.

#### Scenario: Vào phiên per-insight
- **WHEN** người dùng bấm "Hỏi về tin này" trên tin push rồi nhắn "cái này ảnh hưởng gì đến hệ thống của mình?"
- **THEN** bot xác nhận đang hỏi về insight đó và trả lời theo chế độ per-insight

#### Scenario: Thoát context bằng /reset
- **WHEN** người dùng gửi `/reset` trong khi đang có context insight
- **THEN** bot xóa context, xác nhận, và câu hỏi tiếp theo chạy chế độ toàn cục

#### Scenario: Bấm nút của tin khác khi đang trong phiên
- **WHEN** người dùng đang trong phiên insight X và bấm "Hỏi về tin này" trên tin push của insight Y
- **THEN** context chuyển sang insight Y

### Requirement: History hội thoại per-chat
Bot SHALL lưu tối đa 10 lượt hội thoại gần nhất mỗi chat trong bảng `chat_sessions` và gửi kèm khi gọi chat service để hỗ trợ câu hỏi nối tiếp.

#### Scenario: Câu hỏi nối tiếp trên Telegram
- **WHEN** người dùng hỏi tiếp "vậy nên làm gì trước?" sau một câu trả lời
- **THEN** bot hiểu ngữ cảnh từ history và trả lời nối tiếp đúng chủ đề

### Requirement: Thông báo khi hết quota
Khi chat service trả 429 (hết budget chat trong ngày), bot SHALL gửi thông báo tiếng Việt rõ ràng thay vì im lặng hoặc lỗi kỹ thuật.

#### Scenario: Hết budget trong ngày
- **WHEN** người dùng đặt câu hỏi khi budget chat đã cạn
- **THEN** bot trả lời rằng đã hết lượt hỏi trong ngày và hẹn quay lại hôm sau
