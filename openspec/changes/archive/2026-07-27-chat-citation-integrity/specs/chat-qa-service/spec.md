## MODIFIED Requirements

### Requirement: Citation do server cấp phát, model không phát ra định danh
Service SHALL đánh số các insight candidate là `[1..N]` và giữ bảng ánh xạ `n → insight_id` ở phía server; prompt gửi cho model SHALL KHÔNG chứa UUID của insight. Model SHALL trả lời bằng text thuần, trích dẫn bằng marker `[n]`. Service SHALL dựng `citations` bằng cách tra marker trong bảng ánh xạ; marker ngoài phạm vi `[1..N]` SHALL bị bỏ khỏi câu trả lời nhưng phần còn lại của câu trả lời SHALL được giữ.

Mỗi phần tử `citations` SHALL mang **số marker `n` tường minh** mà server đã cấp phát cho insight đó, bên cạnh `insight_id`, `title`, `source_url`. Service SHALL KHÔNG đánh số lại marker trong câu trả lời: `n` trong answer và `n` trong `citations` SHALL là cùng một con số, để phía hiển thị không phải suy ra `n` từ vị trí trong mảng.

#### Scenario: Câu hỏi có dữ liệu trả lời
- **WHEN** câu hỏi khớp với insight trong hệ thống
- **THEN** answer chứa marker `[n]`, và `citations` được service dựng đầy đủ (`n`, `insight_id`, `title`, `source_url`) từ bảng ánh xạ

#### Scenario: Marker không liền mạch từ 1
- **WHEN** model chỉ trích dẫn `[3]`, `[7]` và `[12]` trong khi index có 60 candidate
- **THEN** `citations` gồm đúng 3 phần tử mang `n` lần lượt là 3, 7, 12 — trỏ đúng insight thứ 3, 7, 12 của index
- **AND** marker trong answer giữ nguyên là `[3]`, `[7]`, `[12]`, không bị đánh số lại thành `[1]`, `[2]`, `[3]`

#### Scenario: Model trích dẫn marker ngoài phạm vi
- **WHEN** model trả về `[99]` trong khi chỉ có 40 candidate
- **THEN** service bỏ marker đó khỏi answer, giữ nguyên phần nội dung còn lại, và không tạo citation tương ứng

#### Scenario: Câu trả lời khẳng định nhưng không có marker nào
- **WHEN** model trả lời mang tính khẳng định mà không có bất kỳ marker `[n]` nào và cũng không phải dạng "không tìm thấy"
- **THEN** service thay câu trả lời bằng thông báo không đủ căn cứ (fail-closed)

#### Scenario: Không tìm thấy dữ liệu
- **WHEN** câu hỏi không khớp insight nào trong index
- **THEN** service trả lời rõ ràng rằng không tìm thấy thông tin trong hệ thống, không suy diễn từ kiến thức ngoài, `citations` rỗng, và câu trả lời KHÔNG bị fail-closed chặn

### Requirement: Xếp hạng hai tầng — liên quan trước, quan trọng sau
Xếp hạng candidate SHALL dùng khoá hai tầng: (1) **độ liên quan** giữa từ khoá câu hỏi và nội dung tin, (2) **độ quan trọng** qua `delivery_engine.score_for_role()`. Khi câu hỏi không chứa từ khoá đặc trưng nào, tầng (1) SHALL hoà và thứ tự SHALL rơi về tầng (2). Việc tách từ khoá SHALL nhận từ dài từ **2 ký tự** trở lên (tiếng Việt đơn âm), lọc nhiễu bằng danh sách stopword chứ không bằng độ dài.

Việc so khớp từ khoá với nội dung tin SHALL thực hiện **theo biên từ**, không theo chuỗi con. Một từ khoá SHALL chỉ tính là khớp khi nó là một từ trọn vẹn trong nội dung tin.

#### Scenario: Tin đúng chủ đề nhưng độ khẩn thấp
- **WHEN** người dùng hỏi về một chủ đề ngách mà các tin liên quan đều có `recommendations[role].urgency` thấp, trong khi hệ thống có tin khẩn thuộc chủ đề khác
- **THEN** tin đúng chủ đề SHALL xếp trên tin khẩn lạc đề, và SHALL nằm trong index kể cả khi có trần top-K

#### Scenario: Câu hỏi chung chung
- **WHEN** người dùng hỏi "có gì mới không?" (không từ khoá đặc trưng)
- **THEN** thứ tự index theo `score_for_role()`, tin quan trọng nhất lên đầu

#### Scenario: Từ khoá ngắn không khớp nhầm vào giữa từ khác
- **WHEN** người dùng hỏi câu chứa từ khoá `AI`
- **THEN** chỉ tin thực sự nhắc tới `AI` như một từ trọn vẹn được tính là liên quan
- **AND** tin chỉ chứa `AI` bên trong từ khác (`email`, `domain`, `training`, `detail`) SHALL KHÔNG được tính là liên quan vì lý do đó
