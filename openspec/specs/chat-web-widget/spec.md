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

Widget SHALL giữ **một luồng hội thoại** cho cả phiên. `history` gửi kèm mỗi câu hỏi SHALL là các lượt của
luồng đó.

Bất biến chống lẫn ngữ cảnh SHALL được bảo đảm bằng **ngữ cảnh đầy đủ** thay vì bằng sự cô lập: mọi insight
được nhắc tới trong `history` SHALL còn mặt trong ngữ cảnh của lượt hiện tại — hoặc trong working set, hoặc
trong phần index toàn hệ thống mà service dựng. Widget SHALL KHÔNG đưa phần câu trả lời đang stream (chưa
chốt) vào `history` của lượt sau.

**Lý do đảo bất biến cũ:** cô lập theo scope chặn được context drift, nhưng chính việc tách đôi làm hai bài
người dùng đã đọc riêng không bao giờ nằm chung một luồng — câu "so sánh hai bài vừa rồi" trở nên không thể
trả lời (đo 28/07/2026: recall@5 = 0/4). Drift cũ là một **mâu thuẫn** giữa `history` và ngữ cảnh; khi cả
hai bài đều nằm trong ngữ cảnh thì mâu thuẫn đó không còn tồn tại để phải chặn.

#### Scenario: Đổi bài rồi hỏi câu nối tiếp mập mờ
- **WHEN** người dùng xem bài A, hỏi một câu, chuyển sang bài B, rồi hỏi "rủi ro của nó thì sao?"
- **THEN** cả A và B đều có mặt trong ngữ cảnh gửi lên, và câu trả lời chỉ rõ đang nói về bài nào

#### Scenario: Rời trang chi tiết không xoá ngữ cảnh
- **WHEN** người dùng đã hỏi về một bài rồi rời trang chi tiết về danh sách
- **THEN** bài đó vẫn nằm trong working set và câu hỏi tiếp theo vẫn tham chiếu được tới nó

#### Scenario: Câu trả lời chưa chốt không lọt vào lịch sử
- **WHEN** một câu trả lời đang stream thì người dùng gửi câu hỏi mới sau khi nó chốt
- **THEN** lịch sử chỉ chứa nội dung đã chốt, không chứa phần dở dang

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

### Requirement: Working set insight hiển thị và sửa được

Widget SHALL duy trì một **working set** các insight đang được đưa vào ngữ cảnh hội thoại, và SHALL gửi
danh sách này kèm mỗi câu hỏi, **tách biệt** với văn bản câu hỏi.

Insight SHALL được thêm vào working set khi người dùng mở trang chi tiết của nó, và khi người dùng bấm vào
một trích dẫn trong câu trả lời. Widget SHALL hiển thị working set dưới dạng danh sách nhãn đọc được, mỗi
mục SHALL bỏ được bằng một thao tác. Khi working set vượt số ô sâu của service, widget SHALL giữ các mục
mới nhất.

Khi working set không rỗng, widget SHALL KHÔNG gửi kèm định danh bài đang xem theo cơ chế cũ — bài đang
xem đã nằm trong working set, gửi cả hai sẽ khiến service đi đường per-insight thay vì đường working set.

Actor: người dùng dashboard. Tiền điều kiện: widget đang mở.

#### Scenario: Đọc hai bài rồi so sánh
- **WHEN** người dùng mở insight A, mở tiếp insight B, rồi hỏi "so sánh hai cái này"
- **THEN** cả A và B đều nằm trong working set gửi lên, và câu trả lời đối chiếu đúng hai bài đó

#### Scenario: Bấm trích dẫn đưa bài vào ngữ cảnh
- **WHEN** người dùng bấm một trích dẫn `[n]` trong câu trả lời
- **THEN** insight tương ứng được thêm vào working set và các câu hỏi tiếp theo có thể nhắc tới nó

#### Scenario: Bỏ một mục khỏi working set
- **WHEN** người dùng bỏ một mục trong working set rồi hỏi tiếp
- **THEN** câu hỏi được gửi đi không còn tham chiếu tới insight đó

#### Scenario: Working set thay cho định danh bài đang xem
- **WHEN** người dùng đang ở trang chi tiết một insight và working set không rỗng
- **THEN** câu hỏi gửi lên mang working set và KHÔNG mang định danh bài đang xem theo cơ chế cũ
