# chat-web-widget

## Purpose

Bề mặt người dùng của chatbot: một panel chat nổi ở góc dashboard, có mặt trên mọi trang và tự biết
người dùng đang xem insight nào. Widget quyết định chế độ hỏi (per-insight hay toàn cục) bằng context
chip, giữ history hội thoại phía client, và render citation của bot thành link mở chi tiết insight.

Chat chỉ sống trên dashboard — không có route riêng, không có bề mặt Telegram/email. Phần backend nằm
ở capability `chat-qa-service`.
## Requirements
### Requirement: Widget chat nổi trên mọi trang
Frontend SHALL hiển thị nút mở chat ở góc phải dưới trên mọi trang của dashboard. Bấm nút SHALL mở panel chat (~380px trên desktop); panel SHALL đóng/mở được mà không mất nội dung hội thoại trong phiên. Widget SHALL không tự động mở.

#### Scenario: Mở và đóng widget
- **WHEN** người dùng bấm nút chat ở góc màn hình
- **THEN** panel chat mở; bấm đóng thì panel ẩn nhưng hội thoại còn nguyên khi mở lại trong cùng phiên

#### Scenario: Không che thao tác chính
- **WHEN** panel chat đang mở trên desktop
- **THEN** người dùng vẫn cuộn và thao tác được với danh sách/chi tiết insight phía sau

### Requirement: Context chip theo insight đang mở
Khi người dùng đang ở trang chi tiết một insight (`/insights/:id`), widget SHALL tự gắn context chip hiển thị title insight đó và gửi `insight_id` kèm câu hỏi (chế độ B). Người dùng SHALL bỏ được chip (✕) để chuyển sang hỏi toàn cục. Khi rời trang chi tiết, widget SHALL trở về chế độ toàn cục.

Việc đổi ngữ cảnh — chuyển sang insight khác, bỏ chip, hoặc rời trang chi tiết — SHALL đổi luôn scope hội thoại đang hoạt động, để chip đang hiển thị và `history` được gửi luôn thuộc cùng một scope.

#### Scenario: Tự gắn context khi xem detail
- **WHEN** người dùng mở chi tiết insight rồi mở widget và đặt câu hỏi
- **THEN** request gửi kèm `insight_id` của insight đang xem và chip hiển thị title insight

#### Scenario: Bỏ context chip
- **WHEN** người dùng bấm ✕ trên context chip
- **THEN** câu hỏi tiếp theo gửi không kèm `insight_id` (chế độ toàn cục)
- **AND** câu hỏi đó chạy trên luồng toàn cục, không mang `history` về insight vừa bỏ chip

#### Scenario: Chuyển insight đang xem
- **WHEN** người dùng chuyển sang xem insight khác trong khi widget mở
- **THEN** context chip cập nhật theo insight mới
- **AND** widget chuyển sang luồng hội thoại của insight mới, không hiển thị lượt của insight cũ

#### Scenario: Quay về danh sách
- **WHEN** người dùng rời trang chi tiết về danh sách trong khi widget mở
- **THEN** context chip biến mất và câu hỏi tiếp theo chạy chế độ toàn cục trên luồng toàn cục

### Requirement: Render citation thành link
Câu trả lời của bot SHALL hiển thị citations dưới dạng link; bấm citation SHALL điều hướng đến chi tiết insight tương ứng trong dashboard.

#### Scenario: Bấm citation
- **WHEN** bot trả lời kèm citation
- **THEN** citation hiển thị title insight dạng link, bấm vào mở chi tiết insight đó

### Requirement: Trạng thái chờ và lỗi
Widget SHALL hiển thị trạng thái đang xử lý trong khi chờ trả lời, và thông báo lỗi tiếng Việt kèm khả năng hỏi lại khi API lỗi hoặc hết quota (429).

#### Scenario: Hết quota chat
- **WHEN** API trả về 429
- **THEN** widget hiển thị thông báo hết lượt hỏi trong ngày bằng tiếng Việt, không mất hội thoại

#### Scenario: Lỗi mạng
- **WHEN** request chat thất bại vì lỗi mạng/server
- **THEN** widget hiển thị lỗi và cho phép gửi lại câu hỏi vừa nhập

### Requirement: Cô lập hội thoại theo ngữ cảnh

Widget SHALL cô lập hội thoại theo **ngữ cảnh (scope)**, trong đó một scope là một `insight_id` cụ thể
(chế độ B) hoặc toàn cục (chế độ A). Mỗi scope SHALL có luồng hội thoại riêng; khi người dùng đổi scope,
widget SHALL hiển thị luồng của scope mới (rỗng nếu scope đó chưa từng được hỏi) và SHALL KHÔNG kéo theo
các lượt của scope trước.

`history` gửi kèm mỗi câu hỏi SHALL chỉ gồm các lượt thuộc scope hiện tại. Widget SHALL KHÔNG bao giờ gửi
lượt của một scope khác làm ngữ cảnh cho câu hỏi ở scope hiện tại. Toàn cục SHALL là **một** scope có luồng
riêng, không phải trạng thái "không có ngữ cảnh" gom chung với mọi lần hỏi toàn cục khác.

Việc cô lập SHALL không làm mất luồng của scope cũ trong cùng phiên: quay lại một scope đã hỏi trước đó
SHALL thấy lại đúng luồng của nó.

#### Scenario: Đổi insight rồi hỏi câu nối tiếp
- **WHEN** người dùng hỏi về insight A, chuyển sang xem insight B, rồi hỏi một câu nối tiếp mập mờ ("rủi ro của nó là gì")
- **THEN** `history` gửi kèm câu hỏi này SHALL KHÔNG chứa lượt nào của insight A
- **AND** câu hỏi chạy trên ngữ cảnh insight B với `insight_id` của B

#### Scenario: Quay lại scope đã hỏi
- **WHEN** người dùng đã hỏi ở insight A, sang B, rồi quay lại A
- **THEN** widget hiển thị lại đúng luồng hội thoại của A, và câu hỏi tiếp theo mang `history` của A

#### Scenario: Toàn cục là một scope riêng
- **WHEN** người dùng bỏ context chip (hoặc rời trang chi tiết) và đặt câu hỏi toàn cục
- **THEN** `history` gửi kèm SHALL KHÔNG chứa lượt hỏi về bất kỳ insight cụ thể nào đang/đã mở

