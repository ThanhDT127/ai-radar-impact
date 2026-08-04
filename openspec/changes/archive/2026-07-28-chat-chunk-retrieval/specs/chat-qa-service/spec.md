## ADDED Requirements

### Requirement: Tín hiệu tương đồng ở mức đoạn văn bản gốc tham gia xếp hạng

Hệ thống SHALL duy trì các đoạn (chunk) của nội dung bài gốc kèm embedding, và tầng độ‑liên‑quan của xếp
hạng toàn cục SHALL nhận thêm một tín hiệu thứ ba: thứ hạng tương đồng giữa câu hỏi và các đoạn đó. Ba tín
hiệu (lexical, vector mức insight, vector mức đoạn) SHALL được trộn bằng cùng cơ chế Reciprocal Rank
Fusion đang dùng; `score_for_role()` SHALL giữ vai trò khoá phụ; và service SHALL cắt top‑K **sau** khi
xếp hạng.

Một insight SHALL nhận thứ hạng của **đoạn khớp tốt nhất** thuộc về nó, KHÔNG phải trung bình các đoạn.

Service SHALL KHÔNG áp ngưỡng similarity để loại insight khỏi tập ứng viên.

Actor: người dùng hỏi ở chế độ toàn hệ thống.

#### Scenario: Định danh chỉ xuất hiện trong thân bài
- **WHEN** người dùng hỏi bằng một định danh chỉ có trong nội dung bài gốc (mã lỗi, tên gói, số phiên bản) mà không có trong phần phân tích
- **THEN** insight chứa bài đó được xếp đủ cao để nằm trong index gửi cho model

#### Scenario: Bài dài không bị phạt vì có nhiều đoạn lạc đề
- **WHEN** một bài dài có một đoạn khớp rất sát câu hỏi và nhiều đoạn không liên quan
- **THEN** insight của bài đó nhận thứ hạng theo đoạn khớp tốt nhất, không bị kéo xuống bởi các đoạn còn lại

#### Scenario: Không có ngưỡng loại insight
- **WHEN** không đoạn nào đạt độ tương đồng cao
- **THEN** service vẫn xếp hạng và trả về top‑K, không trả danh sách rỗng

### Requirement: Đoạn văn bản không phải đích của trích dẫn

Đoạn văn bản gốc SHALL chỉ tham gia tầng xếp hạng. Prompt gửi cho model SHALL KHÔNG chứa đoạn nào như một
mục nguồn được đánh số riêng, và bảng ánh xạ marker `n → nguồn` SHALL tiếp tục chỉ trỏ tới insight.

Nội dung bài gốc đưa vào câu trả lời SHALL tiếp tục đến từ cơ chế ô sâu hiện hành, không đến từ tầng đoạn.

> ⚠️ **Ranh giới này nói về NGUỒN của nội dung, không phải về việc tin nào được rót sâu.** Tầng
> đoạn chữa **truy hồi** nhưng không tự nó mang bằng chứng vào prompt: một tin được kéo lên hạng
> 4 vẫn chỉ vào dưới dạng dòng index nén của phần *phân tích* — nơi không chứa định danh người
> dùng hỏi — nên câu trả lời đúng vẫn là từ chối. Cách đóng khoảng này là **đổi tin nào được ô
> sâu rót** (xem requirement sửa đổi bên dưới), chứ không phải đưa đoạn vào prompt như một nguồn.

#### Scenario: Nhiều đoạn cùng một bài khớp câu hỏi
- **WHEN** ba đoạn của cùng một bài đều khớp câu hỏi
- **THEN** bài đó xuất hiện đúng một lần trong context với đúng một số thứ tự

#### Scenario: Trích dẫn vẫn giải được về insight
- **WHEN** model in một marker nguồn trong câu trả lời
- **THEN** marker đó giải được thành một insight có thật, như hành vi hiện hành

### Requirement: Vòng đời đoạn văn bản và suy giảm êm

Hệ thống SHALL sinh đoạn và embedding cho bài gốc trong luồng xử lý nền, SHALL cho phép backfill idempotent,
và SHALL xoá đoạn cùng lúc với việc xoá nội dung bài gốc theo chính sách lưu trữ.

Lỗi sinh đoạn hoặc embedding SHALL KHÔNG chặn việc tạo insight. Insight chưa có đoạn SHALL vẫn cạnh tranh
đầy đủ ở hai tín hiệu còn lại và SHALL KHÔNG bị phạt ngầm.

Lượt gọi sinh embedding cho đoạn SHALL KHÔNG tính vào ngân sách lượt gọi của chat hay của analysis.

#### Scenario: Insight chưa được chunk
- **WHEN** một insight `published` chưa có đoạn nào
- **THEN** insight đó vẫn tham gia xếp hạng bình thường và có thể lọt top‑K

#### Scenario: Nội dung bài gốc hết hạn lưu trữ
- **WHEN** nội dung bài gốc bị xoá theo chính sách lưu trữ
- **THEN** các đoạn của bài đó cũng bị xoá và không còn tham gia xếp hạng

#### Scenario: Lỗi sinh đoạn khi publish
- **WHEN** việc sinh đoạn hoặc embedding thất bại lúc publish một insight
- **THEN** insight vẫn được tạo, hệ thống ghi cảnh báo, và bài đó backfill được sau

## MODIFIED Requirements

### Requirement: Rót ô sâu tất định cho context

Service SHALL dựng context gồm một số cố định **ô sâu** (cấu hình được) và phần index nén còn lại. Ô sâu
SHALL được lấp theo thứ tự: các insight được tham chiếu trước; **kế đó là insight giữ đoạn văn bản gốc khớp
nhất trên toàn kho, nếu có**; sau đó là các insight xếp hạng cao nhất cho tới khi đầy. Insight đã nằm trong
ô sâu SHALL bị loại khỏi phần index để một insight không mang hai số.

Ô sâu SHALL mang đầy đủ các trường phân tích của insight và nội dung bài gốc khi còn lưu trữ; phần index
SHALL giữ dạng nén như hiện hành. Toàn bộ context SHALL dùng **một dãy số liên tục** và **một bảng ánh xạ**
`n → insight`.

Suất dành cho đoạn khớp nhất SHALL chỉ được cấp khi có **đúng một** insight giữ vị trí khớp nhất; nhiều
insight đồng hạng nhất thì SHALL không cấp cho ai. Suất này SHALL KHÔNG làm tăng tổng số ô sâu, và SHALL
KHÔNG áp dụng ở chế độ mở rộng (nơi ô sâu duy nhất là bài người dùng đang xem).

Việc lấp ô sâu SHALL KHÔNG phụ thuộc vào bất kỳ phép phân loại ý định hay phán đoán "câu hỏi này có cần
chi tiết không" nào. Vị trí khớp nhất ở mức đoạn là một đại lượng **đo được từ dữ liệu**, không phải một
phán đoán về câu hỏi.

#### Scenario: Câu hỏi chi tiết không có tham chiếu
- **WHEN** người dùng hỏi một chi tiết chỉ có trong thân bài (ví dụ tên gói bị chèn mã độc) mà không ghim bài nào
- **THEN** các insight xếp hạng cao nhất được rót ở độ sâu đầy đủ và câu trả lời nêu được chi tiết đó thay vì tuyên bố hệ thống không có thông tin

#### Scenario: Ô sâu lấp lẫn tham chiếu và tin xếp hạng
- **WHEN** người dùng ghim ít insight hơn số ô sâu
- **THEN** phần ô sâu còn trống được lấp bằng insight xếp hạng cao nhất chưa được ghim

#### Scenario: Không trùng số giữa ô sâu và index
- **WHEN** một insight vừa được ghim vừa nằm trong nhóm xếp hạng cao
- **THEN** insight đó xuất hiện đúng một lần, ở ô sâu, và không xuất hiện lại trong phần index

#### Scenario: Bài khớp nhất ở mức đoạn nhưng thứ hạng tổng thấp
- **WHEN** một insight có đoạn văn bản gốc khớp nhất toàn kho nhưng thứ hạng tổng của nó nằm ngoài số ô sâu
- **THEN** insight đó vẫn được rót ở độ sâu đầy đủ và câu trả lời nêu được chi tiết nằm trong thân bài của nó

#### Scenario: Người dùng ghim đủ số ô sâu
- **WHEN** số insight được tham chiếu đã lấp kín ô sâu
- **THEN** tin khớp nhất ở mức đoạn không chen được vào, và lựa chọn của người dùng được giữ nguyên
