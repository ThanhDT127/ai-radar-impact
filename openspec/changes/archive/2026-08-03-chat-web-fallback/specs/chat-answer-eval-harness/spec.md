## ADDED Requirements

### Requirement: Kết quả tra cứu ngoài được đông lạnh để harness giữ tính tất định

Bộ đo chất lượng câu trả lời SHALL KHÔNG gọi tra cứu ngoài thật khi chạy. Kết quả bước tra cứu
(danh sách uri, tiêu đề) và **văn bản đã tải về** SHALL được đông lạnh theo kịch bản.

Fixture đông lạnh SHALL mang **dòng vân tay** gồm truy vấn, danh sách uri và ngày lấy; bộ nạp
SHALL **báo lỗi dừng** khi vân tay lệch với kịch bản hiện có, thay vì lặng lẽ chấm trên dữ liệu
mốc.

Lý do: nội dung web đổi theo thời gian, nên gọi thật vừa làm bộ đo không tái lập được, vừa tốn
tiền theo số lần chạy — mà bộ đo là thứ cần chạy nhiều lần.

#### Scenario: Chạy offline
- **WHEN** chạy harness ở chế độ chấm lại snapshot
- **THEN** không lượt tra cứu nào được thực hiện và kết quả tất định

#### Scenario: Vân tay lệch
- **WHEN** kịch bản đổi hoặc fixture cũ hơn tập kịch bản hiện tại
- **THEN** bộ nạp báo lỗi dừng, KHÔNG chấm tiếp

### Requirement: Nhóm kịch bản cho câu hỏi có căn cứ một phần

Tập kịch bản SHALL có một nhóm dành cho câu hỏi **ghép nhiều vế mà chỉ một vế có căn cứ** trong
corpus.

Nhóm này SHALL được chấm theo tiêu chí *có trả lời được vế có dữ liệu hay không*, KHÔNG chấm
như nhóm từ chối — ở đây từ chối toàn bộ là **sai**, không phải đúng.

#### Scenario: Câu hỏi một vế có, một vế không
- **WHEN** chấm một kịch bản thuộc nhóm này
- **THEN** câu trả lời từ chối toàn bộ bị tính là **trượt**

### Requirement: Đo tỉ lệ sentinel giả trước khi bật mặc định

SHALL có phép đo tỉ lệ **sentinel giả** — số lần model yêu cầu tra cứu ngoài trên các câu hỏi
vốn trả lời được hoàn toàn từ corpus.

Sentinel giả tốn tiền tra cứu và nhân đôi độ trễ, nên tỉ lệ này SHALL được đo và ghi lại trước
khi bật tính năng ở mặc định.

#### Scenario: Bộ câu hỏi trả lời được hoàn toàn từ corpus
- **WHEN** chạy phép đo trên bộ câu hỏi này
- **THEN** số lượt phát sentinel tra cứu được đếm và ghi vào tài liệu đo lường

## MODIFIED Requirements

### Requirement: Ngưỡng gate và baseline đóng băng, báo cáo theo từng kịch bản

Bộ đo SHALL cho một verdict PASS/FAIL theo ngưỡng: **Faithfulness ≥ 0,95** và **Citation Precision = 1,00**;
**Answer Relevance** SHALL đóng băng baseline kèm dung sai khai báo tường minh và báo cáo per‑kịch‑bản. Cập
nhật baseline SHALL là hành động có chủ đích kèm lý do ghi lại, SHALL KHÔNG làm để test chuyển xanh.

Hai ngưỡng cứng SHALL tính trên **toàn bộ** câu trả lời, kể cả phần dựa trên nguồn tra cứu ngoài.

Điều này đo được vì nội dung web **nằm trong ngữ cảnh** đưa cho model, chứ không phải kiến thức
sẵn có của model. Nếu nội dung nguồn không nằm trong ngữ cảnh thì hai chỉ số này mất cơ sở đo
và cổng chất lượng thành hình thức.

Không đạt ngưỡng SHALL dẫn tới sửa code, KHÔNG hạ ngưỡng.

#### Scenario: Câu trả lời trích cả nguồn hệ thống và nguồn web
- **WHEN** chấm một câu trả lời có dùng nguồn web
- **THEN** mọi khẳng định đều được đối chiếu với ngữ cảnh đã đưa vào, gồm cả văn bản trang web
