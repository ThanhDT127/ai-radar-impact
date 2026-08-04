## ADDED Requirements

### Requirement: Nhận tham chiếu insight có cấu trúc, tách khỏi câu hỏi

Endpoint chat SHALL nhận một danh sách tham chiếu insight (`referenced_insight_ids`) **tách biệt** với
trường câu hỏi. Service SHALL nạp các insight đó từ dữ liệu và đưa vào context của lượt trả lời.

Prompt gửi cho model SHALL KHÔNG chứa định danh insight (UUID, URL nội bộ) dưới bất kỳ dạng nào — tham
chiếu SHALL được server chuyển thành số thứ tự `[n]` theo đúng cơ chế cấp phát định danh hiện hành. Việc
nhận tham chiếu SHALL KHÔNG làm thay đổi cách tính từ khoá của câu hỏi.

Actor: người dùng dashboard. Tiền điều kiện: insight được tham chiếu đã `published`.

#### Scenario: So sánh hai insight đã đọc riêng
- **WHEN** người dùng đã mở lần lượt hai insight và hỏi "hai cái này khác nhau chỗ nào?" với cả hai id trong tham chiếu
- **THEN** câu trả lời đối chiếu đúng hai insight đó và trích dẫn cả hai, không phụ thuộc vào việc câu hỏi có chứa từ khoá nội dung hay không

#### Scenario: Tham chiếu không lọt vào phép so khớp từ khoá
- **WHEN** một lượt hỏi có tham chiếu insight
- **THEN** tập từ khoá dùng cho xếp hạng được tính chỉ từ văn bản câu hỏi, không bị thêm định danh hay URL

#### Scenario: Tham chiếu trỏ insight không còn khả dụng
- **WHEN** một tham chiếu trỏ tới insight không tồn tại hoặc không ở trạng thái `published`
- **THEN** service bỏ qua tham chiếu đó và vẫn trả lời bằng các tham chiếu còn lại; không trả lỗi cho người dùng

#### Scenario: Số tham chiếu vượt số ô sâu
- **WHEN** client gửi nhiều tham chiếu hơn số ô sâu cấu hình
- **THEN** service dùng các tham chiếu đầu tiên tới khi đầy ô sâu và bỏ phần dư; không trả lỗi

### Requirement: Rót ô sâu tất định cho context

Service SHALL dựng context gồm một số cố định **ô sâu** (cấu hình được) và phần index nén còn lại. Ô sâu
SHALL được lấp theo thứ tự: các insight được tham chiếu trước, sau đó là các insight xếp hạng cao nhất cho
tới khi đầy. Insight đã nằm trong ô sâu SHALL bị loại khỏi phần index để một insight không mang hai số.

Ô sâu SHALL mang đầy đủ các trường phân tích của insight và nội dung bài gốc khi còn lưu trữ; phần index
SHALL giữ dạng nén như hiện hành. Toàn bộ context SHALL dùng **một dãy số liên tục** và **một bảng ánh xạ**
`n → insight`.

Việc lấp ô sâu SHALL KHÔNG phụ thuộc vào bất kỳ phép phân loại ý định hay phán đoán "câu hỏi này có cần
chi tiết không" nào.

#### Scenario: Câu hỏi chi tiết không có tham chiếu
- **WHEN** người dùng hỏi một chi tiết chỉ có trong thân bài (ví dụ tên gói bị chèn mã độc) mà không ghim bài nào
- **THEN** các insight xếp hạng cao nhất được rót ở độ sâu đầy đủ và câu trả lời nêu được chi tiết đó thay vì tuyên bố hệ thống không có thông tin

#### Scenario: Ô sâu lấp lẫn tham chiếu và tin xếp hạng
- **WHEN** người dùng ghim ít insight hơn số ô sâu
- **THEN** phần ô sâu còn trống được lấp bằng insight xếp hạng cao nhất chưa được ghim

#### Scenario: Không trùng số giữa ô sâu và index
- **WHEN** một insight vừa được ghim vừa nằm trong nhóm xếp hạng cao
- **THEN** insight đó xuất hiện đúng một lần, ở ô sâu, và không xuất hiện lại trong phần index

### Requirement: Marker trong lịch sử hội thoại giải thành tiêu đề

Khi dựng khối lịch sử hội thoại đưa vào prompt, service SHALL thay mọi marker nguồn dạng `[n]` trong các
lượt trước bằng nhãn nhận diện được của insight tương ứng (tiêu đề), thay vì giữ nguyên con số.

Lý do: bảng ánh xạ `n → insight` được dựng lại theo từng lượt, nên một con số trong lịch sử có thể trỏ
insight khác ở lượt hiện tại.

#### Scenario: Số marker bị tái sử dụng qua các lượt
- **WHEN** một lượt trước trích `[3]` cho insight X và lượt hiện tại đánh số `[3]` cho insight Y
- **THEN** khối lịch sử đưa vào prompt nhắc tới X bằng tiêu đề, và model không hiểu nhầm `[3]` của lượt trước là Y

### Requirement: Hình dạng câu trả lời cho câu hỏi đối chiếu

Khi context có từ hai ô sâu trở lên, hướng dẫn trả lời SHALL cho phép trình bày dạng **đối chiếu theo
chiều so sánh** thay vì bắt buộc mỗi tin gói trong một gạch đầu dòng. Trần số tin tối đa cho một câu trả
lời SHALL giữ nguyên, và mọi khẳng định SHALL vẫn kèm marker nguồn.

#### Scenario: Câu hỏi so sánh hai insight
- **WHEN** người dùng hỏi so sánh và context có hai ô sâu
- **THEN** câu trả lời nêu các chiều khác biệt cụ thể giữa hai insight, không phải hai đoạn mô tả rời nhau

#### Scenario: Câu hỏi thường không đổi hình dạng
- **WHEN** người dùng hỏi một câu tra cứu bình thường
- **THEN** câu trả lời giữ đúng độ dài và hình dạng như hiện hành

## MODIFIED Requirements

### Requirement: Endpoint chat hai chế độ

Hệ thống SHALL cung cấp endpoint `POST /api/v1/chat` nhận
`{ question, history, insight_id?, referenced_insight_ids? }` và trả về `{ answer, citations, mode }`.

Trước khi chọn chế độ, service SHALL chạy định tuyến ý định: khi câu hỏi là chào hỏi/meta/cảm ơn, service
SHALL trả `mode="meta"` với câu định sẵn và không gọi model. Ngược lại service SHALL chọn chế độ theo thứ
tự ưu tiên:

- có ít nhất một tham chiếu insight còn khả dụng → chế độ working set (`mode="focused"`), **một** lượt
  trả lời, context gồm ô sâu + index toàn hệ thống, KHÔNG dùng cơ chế sentinel/mở rộng;
- không có tham chiếu nhưng có `insight_id` → chế độ per-insight (`mode="insight"`), giữ nguyên cơ chế
  auto‑fallback sang `mode="expanded"`;
- không có cả hai → chế độ toàn cục (`mode="global"`).

Tham chiếu insight SHALL được nhận qua trường riêng, KHÔNG nhúng vào văn bản câu hỏi.

#### Scenario: Hỏi với working set
- **WHEN** request mang tham chiếu tới hai insight còn khả dụng
- **THEN** service trả `mode="focused"` trong một lượt trả lời, và câu trả lời trích dẫn được cả hai

#### Scenario: Không có tham chiếu thì giữ nguyên hành vi cũ
- **WHEN** request không mang tham chiếu nào
- **THEN** service chọn chế độ per-insight hoặc toàn cục đúng như trước, kể cả cơ chế auto‑fallback

#### Scenario: Tham chiếu được ưu tiên hơn định danh bài đang xem
- **WHEN** request mang cả tham chiếu lẫn `insight_id`
- **THEN** service chạy chế độ working set; bài đang xem không bị bỏ sót vì client đã đưa nó vào tham chiếu
