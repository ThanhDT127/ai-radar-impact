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

Widget SHALL giải marker `[n]` trong câu trả lời bằng **số marker `n` do server cấp phát**, KHÔNG bằng vị trí của phần tử trong mảng `citations`. Danh sách nguồn hiển thị kèm câu trả lời SHALL đánh số **khớp với marker trong câu**, không tự đánh số lại. Marker không tìm được citation tương ứng SHALL hiển thị như text thường, KHÔNG bao giờ trỏ sang insight khác.

#### Scenario: Bấm citation
- **WHEN** bot trả lời kèm citation
- **THEN** citation hiển thị title insight dạng link, bấm vào mở chi tiết insight đó

#### Scenario: Marker không liền mạch từ 1
- **WHEN** câu trả lời chứa marker `[3]`, `[7]`, `[12]` và `citations` mang `n` tương ứng 3, 7, 12
- **THEN** bấm `[3]` mở đúng insight có `n = 3`, bấm `[7]` mở đúng insight có `n = 7`, bấm `[12]` mở đúng insight có `n = 12`

#### Scenario: Marker xuất hiện không theo thứ tự tăng dần
- **WHEN** câu trả lời nhắc `[5]` trước rồi mới tới `[2]`
- **THEN** mỗi marker vẫn mở đúng insight mang `n` bằng chính con số đó, không hoán đổi cho nhau

#### Scenario: Danh sách nguồn khớp marker trong câu
- **WHEN** câu trả lời trích dẫn các insight mang `n` là 3, 7, 12
- **THEN** danh sách nguồn dưới câu trả lời hiển thị `[3]`, `[7]`, `[12]` — cùng con số với marker trong câu

#### Scenario: Marker không có citation tương ứng
- **WHEN** answer còn sót một marker mà `citations` không có phần tử `n` khớp
- **THEN** marker đó hiển thị như text thường, không thành link, và không trỏ tới insight nào khác

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

### Requirement: Chỉ báo phạm vi và chuyển scope hai chiều

Khi người dùng đang ở trang chi tiết một insight, widget SHALL hiển thị **chỉ báo phạm vi (scope)** hiện
tại — "Bài đang xem" hoặc "Toàn hệ thống" — và SHALL cho phép chuyển đổi **hai chiều** giữa hai phạm vi đó
bằng một thao tác, **không cần điều hướng trang**. Đây là cơ chế chuyển scope tường minh, thay cho việc bỏ
context chip một chiều.

Chuyển phạm vi SHALL đổi luồng hội thoại tương ứng theo cơ chế cô lập scope (mỗi scope một luồng riêng);
widget SHALL KHÔNG mang lượt của scope này sang scope kia.

Câu trả lời được service mở rộng tự động (`mode="expanded"`) SHALL được đánh dấu để người dùng biết nó dựa
trên tìm kiếm **toàn hệ thống**, không chỉ bài đang xem.

#### Scenario: Hiển thị scope hiện tại
- **WHEN** người dùng mở widget khi đang ở trang chi tiết một insight
- **THEN** widget hiển thị chỉ báo phạm vi cho biết đang hỏi trong phạm vi "Bài đang xem"

#### Scenario: Chuyển scope hai chiều
- **WHEN** người dùng bấm chuyển sang "Toàn hệ thống" rồi bấm chuyển lại "Bài đang xem"
- **THEN** mỗi lần bấm đổi phạm vi ngay tại chỗ, không rời trang, và câu hỏi tiếp theo chạy đúng phạm vi đang hiển thị

#### Scenario: Chuyển scope đổi luồng hội thoại
- **WHEN** người dùng chuyển từ "Bài đang xem" sang "Toàn hệ thống"
- **THEN** widget hiển thị luồng hội thoại của scope toàn cục, không hiển thị lượt hỏi về bài; `history` gửi kèm không chứa lượt của scope bài

#### Scenario: Đánh dấu câu trả lời mở rộng
- **WHEN** service trả về câu trả lời với `mode="expanded"`
- **THEN** widget đánh dấu bong bóng trả lời đó là kết quả tìm trên toàn hệ thống, phân biệt với trả lời trong phạm vi bài

### Requirement: Render câu trả lời theo luồng với trạng thái tiến trình

Widget SHALL tiêu thụ endpoint streaming và render câu trả lời **tăng dần** khi token đến, thay cho việc chờ
trọn câu rồi hiện một lần. Trong lúc chờ, widget SHALL hiển thị **trạng thái tiến trình** do server phát (ví
dụ đang tìm trong hệ thống, đang tìm toàn hệ thống) thay cho một spinner đơn.

Khi nhận sự kiện chốt, widget SHALL gắn danh sách citation vào câu trả lời; nếu sự kiện chốt là fail‑closed,
widget SHALL **thay** phần text đã stream bằng nội dung không‑đủ‑căn‑cứ, KHÔNG giữ lại text ungrounded. Widget
SHALL vô hiệu hoá nút gửi trong khi một câu trả lời đang stream để tránh gửi trùng.

Nếu người dùng đổi scope hoặc rời ngữ cảnh trong khi một câu trả lời đang stream, widget SHALL huỷ luồng đang
chạy và SHALL KHÔNG nhập phần text dở vào luồng hội thoại của scope mới.

#### Scenario: Câu trả lời chảy dần kèm trạng thái
- **WHEN** người dùng gửi câu hỏi và server đang xử lý
- **THEN** widget hiện trạng thái tiến trình rồi các phần câu trả lời xuất hiện dần, và citations gắn vào khi luồng chốt

#### Scenario: Fail‑closed hoán text
- **WHEN** sự kiện chốt báo câu trả lời không đủ căn cứ
- **THEN** widget thay phần đã stream bằng thông báo không‑đủ‑căn‑cứ, không để lại nội dung ungrounded

#### Scenario: Đổi scope khi đang stream
- **WHEN** người dùng đổi insight hoặc chuyển scope trong khi câu trả lời đang stream
- **THEN** widget huỷ luồng đang chạy và luồng hội thoại của scope mới không chứa phần text dở

#### Scenario: Chống gửi trùng khi đang stream
- **WHEN** một câu trả lời đang được stream
- **THEN** nút gửi bị vô hiệu hoá cho tới khi luồng kết thúc

