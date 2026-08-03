## ADDED Requirements

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

## MODIFIED Requirements

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
