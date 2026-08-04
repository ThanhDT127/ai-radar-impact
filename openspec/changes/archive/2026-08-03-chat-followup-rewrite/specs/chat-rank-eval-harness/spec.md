## ADDED Requirements

### Requirement: Kịch bản mang lịch sử hội thoại

Bộ kịch bản SHALL hỗ trợ kịch bản có **lịch sử hội thoại** — câu hỏi lượt trước và các nguồn đã
được trích ở lượt đó — chứ không chỉ câu hỏi đơn lẻ.

Đây là khoảng trống có thật ở thời điểm mở change: **0/98** kịch bản mang lịch sử, nên không lưới
thường trực nào canh đường hội thoại đa lượt — kể cả cơ chế ghim tin đã trích, vốn chỉ chạy khi có
lịch sử. Bộ đo hiện chỉ chứng minh "không hồi quy trên đường một lượt".

#### Scenario: Kịch bản có lịch sử
- **WHEN** một kịch bản khai báo câu hỏi lượt trước và các nguồn đã trích ở lượt đó
- **THEN** bộ đo dựng đúng lịch sử ấy và đo xếp hạng của lượt hiện tại trong ngữ cảnh đó

#### Scenario: Kịch bản không có lịch sử
- **WHEN** một kịch bản không khai báo lịch sử
- **THEN** kết quả trùng khít cách đo trước khi hỗ trợ trường này

### Requirement: Nhóm kịch bản câu nối tiếp cần tin chưa từng bàn

Bộ kịch bản SHALL có một nhóm cho **câu nối tiếp thừa kế chủ đề nhưng cần tin chưa từng được
trích**. Với mọi kịch bản trong nhóm này, tập `must_have` SHALL **rời hoàn toàn** khỏi tập nguồn đã
trích ở các lượt trước, và bộ đo SHALL kiểm điều kiện đó khi nạp, **nổ** nếu vi phạm.

Ràng buộc rời nhau là **định nghĩa của nhóm**, không phải một chi tiết: nếu tin đích từng được
trích thì cơ chế ghim đã bảo đảm nó có mặt, và kịch bản sẽ đo một việc mà xếp hạng không được nhờ
làm — cho điểm cao giả trong khi chế độ hỏng thật vẫn nguyên.

#### Scenario: Nhãn vi phạm định nghĩa nhóm
- **WHEN** một kịch bản trong nhóm có `must_have` giao với nguồn đã trích ở lượt trước
- **THEN** bộ đo báo lỗi rõ ràng khi nạp thay vì chấm điểm cho kịch bản đó

#### Scenario: Tin đích chưa từng được trích
- **WHEN** câu hỏi nối tiếp cần một tin chưa xuất hiện trong bất kỳ lượt nào trước đó
- **THEN** điểm của kịch bản phản ánh đúng năng lực truy hồi, không được cơ chế ghim che
