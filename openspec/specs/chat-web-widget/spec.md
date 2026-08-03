# chat-web-widget

## Purpose

Bề mặt người dùng của chatbot: một panel chat nổi ở góc dashboard, có mặt trên mọi trang và tự biết
người dùng đang xem insight nào. Widget quyết định chế độ hỏi (per-insight hay toàn cục) bằng context
chip, giữ history hội thoại phía client, và render citation của bot thành link mở chi tiết insight.

Chat chỉ sống trên dashboard — không có route riêng, không có bề mặt Telegram/email. Phần backend nằm
ở capability `chat-qa-service`.
## Requirements
### Requirement: Widget chat nổi trên mọi trang
Frontend SHALL hiển thị nút mở chat ở góc phải dưới trên mọi trang của dashboard. Bấm nút SHALL mở panel chat (~380px trên desktop); panel SHALL đóng/mở được mà không mất nội dung hội thoại.

Widget SHALL KHÔNG tự ý mở khi người dùng chưa từng mở nó trong tab hiện tại. Việc **khôi phục
trạng thái mở mà chính người dùng đã để lại** trước khi tải lại trang KHÔNG được tính là tự
động mở.

#### Scenario: Mở và đóng widget
- **WHEN** người dùng bấm nút chat ở góc màn hình
- **THEN** panel chat mở; bấm đóng thì panel ẩn nhưng hội thoại còn nguyên khi mở lại

#### Scenario: Không che thao tác chính
- **WHEN** panel chat đang mở trên desktop
- **THEN** người dùng vẫn cuộn và thao tác được với danh sách/chi tiết insight phía sau

#### Scenario: Chưa từng mở thì không tự bật
- **WHEN** người dùng tải dashboard trong một tab mới và chưa từng mở widget
- **THEN** widget hiển thị dạng nút, panel không tự mở

#### Scenario: Đang mở thì tải lại trang
- **WHEN** panel đang mở và người dùng tải lại trang
- **THEN** panel mở lại cùng nội dung hội thoại

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

Widget SHALL giữ **một luồng hội thoại** cho cả tab. `history` gửi kèm mỗi câu hỏi SHALL là các lượt của
luồng đó.

Luồng hội thoại SHALL **độc lập** với working set và với bài đang xem: các lượt đã trao đổi
SHALL tồn tại độc lập với việc working set có mục nào hay rỗng. Widget SHALL KHÔNG đánh khoá
hay phân mảnh luồng theo scope, bài đang xem, hay nội dung working set.

Bất biến chống lẫn ngữ cảnh SHALL được bảo đảm bằng **ngữ cảnh đầy đủ** thay vì bằng sự cô lập: mọi insight
được nhắc tới trong `history` SHALL còn mặt trong ngữ cảnh của lượt hiện tại — hoặc trong working set, hoặc
trong phần index toàn hệ thống mà service dựng. Widget SHALL KHÔNG đưa phần câu trả lời đang stream (chưa
chốt) vào `history` của lượt sau.

**Lý do đảo bất biến cũ:** cô lập theo scope chặn được context drift, nhưng chính việc tách đôi làm hai bài
người dùng đã đọc riêng không bao giờ nằm chung một luồng — câu "so sánh hai bài vừa rồi" trở nên không thể
trả lời (đo 28/07/2026: recall@5 = 0/4). Drift cũ là một **mâu thuẫn** giữa `history` và ngữ cảnh; khi cả
hai bài đều nằm trong ngữ cảnh thì mâu thuẫn đó không còn tồn tại để phải chặn.

**Vì sao ghi thêm điều kiện độc lập:** phiên bản đầu của widget đánh khoá luồng theo scope, nên
rời bài là luồng của bài đó biến khỏi màn hình. Việc lưu bền luồng mở lại đúng cám dỗ đó —
đánh khoá dữ liệu lưu theo ngữ cảnh cho "gọn" sẽ khiến bỏ hết working set đồng nghĩa với mất
hội thoại.

#### Scenario: Đổi bài rồi hỏi câu nối tiếp mập mờ
- **WHEN** người dùng xem bài A, hỏi một câu, chuyển sang bài B, rồi hỏi "rủi ro của nó thì sao?"
- **THEN** cả A và B đều có mặt trong ngữ cảnh gửi lên, và câu trả lời chỉ rõ đang nói về bài nào

#### Scenario: Rời trang chi tiết không xoá ngữ cảnh
- **WHEN** người dùng đã hỏi về một bài rồi rời trang chi tiết về danh sách
- **THEN** bài đó vẫn nằm trong working set và câu hỏi tiếp theo vẫn tham chiếu được tới nó

#### Scenario: Câu trả lời chưa chốt không lọt vào lịch sử
- **WHEN** một câu trả lời đang stream thì người dùng gửi câu hỏi mới sau khi nó chốt
- **THEN** lịch sử chỉ chứa nội dung đã chốt, không chứa phần dở dang

#### Scenario: Working set rỗng không làm mất luồng
- **WHEN** người dùng đã hỏi vài lượt rồi bỏ hết các mục trong working set
- **THEN** các lượt đó vẫn hiển thị và vẫn được gửi trong `history` của câu hỏi tiếp theo

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

### Requirement: Hội thoại bền vững theo tab

Widget SHALL lưu bền luồng hội thoại theo **tab trình duyệt** và khôi phục nó khi tài liệu được
tải lại trong cùng tab đó: tải lại trang (F5), quay lại bằng back/forward từ một trang ngoài
ứng dụng, và khôi phục tab sau khi trình duyệt đóng bất thường.

Nội dung được lưu SHALL gồm: các lượt hỏi–đáp đã chốt kèm **đầy đủ citation của từng lượt**,
working set, và trạng thái đóng/mở panel.

Widget SHALL lưu vào **một khoá duy nhất cho cả tab**. Khoá lưu trữ SHALL KHÔNG chứa scope, bài
đang xem, hay working set. Không thao tác ngữ cảnh nào — bỏ một mục working set, bỏ **hết** các
mục, đổi bài đang xem, điều hướng sang trang khác — được phép làm mất các lượt đã trao đổi.

Widget SHALL KHÔNG chia sẻ luồng hội thoại giữa các tab: hai tab mở cùng lúc SHALL là hai luồng
độc lập.

Widget SHALL KHÔNG lưu phần câu trả lời đang stream (chưa chốt).

Dữ liệu lưu SHALL mang số phiên bản. Khi phiên bản đọc được khác phiên bản hiện hành, widget
SHALL bỏ qua dữ liệu đó và bắt đầu một luồng trống, KHÔNG cố chuyển đổi.

Khi bộ nhớ của trình duyệt không dùng được hoặc thao tác lưu/đọc thất bại, widget SHALL hoạt
động bình thường không kèm khả năng khôi phục, và SHALL KHÔNG hiển thị lỗi.

Actor: người dùng dashboard. Tiền điều kiện: đã có ít nhất một lượt hỏi–đáp đã chốt.

#### Scenario: Tải lại trang giữa cuộc hội thoại
- **WHEN** người dùng đã hỏi vài lượt rồi tải lại trang trong cùng tab
- **THEN** toàn bộ các lượt đã chốt, working set và trạng thái mở panel hiện lại đúng như trước khi tải lại

#### Scenario: Rời sang trang ngoài rồi quay lại
- **WHEN** người dùng điều hướng tới một trang ngoài ứng dụng rồi bấm back về dashboard trong cùng tab
- **THEN** cuộc hội thoại vẫn còn nguyên

#### Scenario: Citation sống sót qua tải lại
- **WHEN** một lượt đã chốt có trích dẫn tin trong hệ thống, và trang được tải lại
- **THEN** lượt đó vẫn mang đủ định danh insight của các trích dẫn, và câu hỏi tiếp theo vẫn ghim được các tin đã bàn

#### Scenario: Bỏ hết working set không đụng tới hội thoại
- **WHEN** người dùng bỏ lần lượt tất cả các mục trong working set
- **THEN** mọi lượt hỏi–đáp đã trao đổi vẫn còn nguyên trên màn hình và trong dữ liệu lưu

#### Scenario: Hai tab là hai luồng
- **WHEN** người dùng mở dashboard ở hai tab và hỏi ở từng tab
- **THEN** mỗi tab chỉ hiển thị luồng của chính nó, không tab nào thấy lượt của tab kia

#### Scenario: Phần đang stream không được lưu
- **WHEN** một câu trả lời đang stream dở
- **THEN** dữ liệu lưu không chứa phần text tạm đó

#### Scenario: Dữ liệu lưu thuộc phiên bản cũ
- **WHEN** widget đọc được dữ liệu mang số phiên bản khác phiên bản hiện hành
- **THEN** widget bắt đầu một luồng trống và không hiển thị lỗi

#### Scenario: Bộ nhớ trình duyệt không dùng được
- **WHEN** thao tác đọc hoặc ghi bộ nhớ trình duyệt ném lỗi
- **THEN** widget vẫn mở, hỏi và trả lời được như bình thường, không hiện thông báo lỗi

### Requirement: Lượt hỏi bị gián đoạn được giữ lại và hỏi lại được

Widget SHALL giữ lại lượt hỏi bị gián đoạn, hiển thị rõ rằng câu trả lời đã bị gián đoạn, và
cung cấp thao tác **hỏi lại**. Lượt hỏi bị gián đoạn là lượt hỏi của người dùng **chưa có câu
trả lời** đứng cuối luồng khôi phục — trường hợp trang bị tải lại trong lúc câu trả lời đang
được sinh.

Widget SHALL nhận biết trạng thái này từ **cấu trúc của luồng** (lượt cuối là lượt của người
dùng), KHÔNG từ một cờ trạng thái được lưu kèm.

Thao tác hỏi lại SHALL gửi lại đúng câu hỏi đó và SHALL KHÔNG nhân đôi lượt hỏi của người dùng
trên màn hình.

Actor: người dùng dashboard. Tiền điều kiện: trang được tải lại trong lúc một câu trả lời đang
stream.

#### Scenario: Tải lại trang khi câu trả lời đang chảy
- **WHEN** người dùng gửi câu hỏi rồi tải lại trang trước khi câu trả lời được chốt
- **THEN** câu hỏi đó vẫn hiện trên màn hình, kèm thông báo câu trả lời bị gián đoạn và thao tác hỏi lại

#### Scenario: Hỏi lại sau gián đoạn
- **WHEN** người dùng dùng thao tác hỏi lại
- **THEN** đúng câu hỏi đó được gửi lại, và màn hình chỉ có **một** bong bóng câu hỏi đó

#### Scenario: Hỏi lại sau lỗi mạng
- **WHEN** một lượt thất bại vì lỗi và người dùng bấm thử lại
- **THEN** câu hỏi được gửi lại và KHÔNG xuất hiện thêm một bong bóng câu hỏi trùng lặp

### Requirement: Bắt đầu cuộc trò chuyện mới

Widget SHALL cung cấp một thao tác **bắt đầu cuộc trò chuyện mới**, đặt trong phần đầu panel,
kích thước tương đương các nút điều khiển panel khác và tách khỏi khu vực nhập câu hỏi.

Thao tác này SHALL xoá toàn bộ các lượt đã trao đổi, xoá working set, và xoá dữ liệu đã lưu của
tab hiện tại.

Thao tác này SHALL KHÔNG đóng panel.

Actor: người dùng dashboard. Tiền điều kiện: widget đang mở.

#### Scenario: Bắt đầu lại từ đầu
- **WHEN** người dùng dùng thao tác bắt đầu cuộc trò chuyện mới
- **THEN** panel hiển thị trạng thái trống như lần mở đầu tiên, working set rỗng, và panel vẫn mở

#### Scenario: Cuộc trò chuyện mới sống sót qua tải lại
- **WHEN** người dùng bắt đầu cuộc trò chuyện mới rồi tải lại trang
- **THEN** luồng vẫn trống, không có lượt cũ nào quay lại

