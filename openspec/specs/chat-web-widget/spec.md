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

Widget SHALL tiêu thụ endpoint streaming và render câu trả lời **tăng dần** khi token đến.
Khi nhận sự kiện chốt, widget SHALL gắn danh sách citation vào câu trả lời; nếu sự kiện chốt là
fail‑closed, widget SHALL **thay** phần text đã stream bằng nội dung không‑đủ‑căn‑cứ. Widget
SHALL vô hiệu hoá nút gửi trong khi một câu trả lời đang stream.

Trong lúc chờ, widget SHALL hiển thị các mốc tiến trình dưới dạng **danh sách tích luỹ**: mốc
đã qua giữ lại ở dạng mờ kèm dấu hoàn thành, mốc hiện tại hiển thị nổi bật.

Trước đây widget hiển thị **một dòng duy nhất bị ghi đè** mỗi khi có mốc mới, nên người dùng
không thấy được chuỗi việc đã diễn ra.

Widget SHALL phân biệt mốc bằng trường `key` của sự kiện, KHÔNG bằng cách so sánh chuỗi hiển
thị — chuỗi mang số liệu nên hai lần phát cùng một mốc luôn khác nhau.

Widget SHALL hiển thị tối đa **4** dòng; vượt quá thì bỏ dòng cũ nhất.

Widget SHALL KHÔNG hiển thị thanh tiến trình dạng phần trăm hay ước lượng thời gian còn lại.

#### Scenario: Nhiều mốc khác nhau đến trong một lượt
- **WHEN** luồng SSE phát nhiều sự kiện `status` với `key` khác nhau
- **THEN** mỗi mốc hiện thành một dòng riêng, các dòng trước vẫn thấy được ở dạng mờ

#### Scenario: Cùng một mốc được phát lại
- **WHEN** hai sự kiện `status` có cùng `key`
- **THEN** dòng tương ứng được cập nhật tại chỗ, không sinh dòng trùng

#### Scenario: Vượt trần số dòng
- **WHEN** số mốc trong một lượt vượt quá 4
- **THEN** widget hiện 4 mốc gần nhất và bỏ dòng cũ nhất

#### Scenario: Câu trả lời được chốt
- **WHEN** sự kiện `commit` tới
- **THEN** toàn bộ khối tiến trình biến mất, chỉ còn câu trả lời cuối

#### Scenario: Chưa có mốc nào
- **WHEN** người dùng vừa bấm Gửi và chưa có sự kiện `status` nào
- **THEN** widget hiển thị dòng chờ mặc định

#### Scenario: Server cũ không gửi `key`
- **WHEN** sự kiện `status` không mang `key`
- **THEN** widget vẫn hiển thị `text` và không báo lỗi

#### Scenario: `key` không nằm trong tập widget biết
- **WHEN** sự kiện `status` mang một `key` widget chưa biết
- **THEN** widget vẫn hiện nó như một dòng mới, KHÔNG bỏ qua

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

### Requirement: Nguồn web hiển thị phân biệt được với nguồn hệ thống

Widget SHALL hiển thị citation trỏ tới nguồn web khác biệt rõ với citation trỏ tới tin trong
hệ thống, tối thiểu bằng tên miền và một liên kết mở ra ngoài.

Lý do: tin trong hệ thống đã qua phân tích và chấm điểm tin cậy; nguồn web thì chưa. Trộn hai
loại vào cùng một kiểu hiển thị là để người dùng gán nhầm mức tin cậy.

Widget SHALL giải marker `[n]` bằng cách **tra theo trường `n`** trong danh sách citation, áp
dụng cho cả hai loại nguồn — KHÔNG dùng vị trí trong mảng.

#### Scenario: Câu trả lời trích cả hai loại nguồn
- **WHEN** câu trả lời chứa marker trỏ tới cả tin hệ thống và nguồn web
- **THEN** mỗi marker giải đúng nguồn của nó, và hai loại hiển thị phân biệt được

#### Scenario: Marker không liền mạch
- **WHEN** các marker trong câu trả lời không bắt đầu từ 1 hoặc bị ngắt quãng
- **THEN** mọi marker vẫn giải đúng nguồn theo `n`

### Requirement: Khối Search Suggestions

Khi câu trả lời có dùng tra cứu ngoài, widget SHALL hiển thị khối Search Suggestions do nhà
cung cấp trả về, kèm câu trả lời.

#### Scenario: Có tra cứu
- **WHEN** phản hồi mang dữ liệu Search Suggestions
- **THEN** widget hiển thị khối đó

#### Scenario: Không tra cứu
- **WHEN** phản hồi không mang dữ liệu Search Suggestions
- **THEN** widget không hiển thị khối nào và bố cục không đổi

