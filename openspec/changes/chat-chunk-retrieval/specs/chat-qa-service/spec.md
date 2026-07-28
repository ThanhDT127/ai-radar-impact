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

> ⚠️ **Hệ quả đã ĐO, không phải suy đoán** (28/07/2026): tầng đoạn chữa **truy hồi**, không chữa
> **bằng chứng**. Một tin được tầng đoạn kéo lên hạng 4 vẫn chỉ vào prompt dưới dạng dòng index
> nén của phần *phân tích* — nơi không chứa định danh mà người dùng hỏi — nên câu trả lời đúng
> vẫn là từ chối. Đo trên 15 kịch bản `detail_discovery`: 13 xếp hạng ≤ `CHAT_DEEP_SLOTS` (3) nên
> trả lời được, 2 xếp hạng 4 nên vẫn bị từ chối. Đây là ranh giới **có chủ đích** của yêu cầu
> này; nới nó là việc của một change khác, kèm phép đo riêng.

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
