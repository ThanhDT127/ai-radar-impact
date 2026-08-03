# chat-answer-eval-harness Specification

## Purpose
TBD - created by archiving change chat-eval-quality-gate. Update Purpose after archive.
## Requirements
### Requirement: Đo Faithfulness và Answer Relevance trên câu trả lời sinh live

Bộ đo SHALL sinh câu trả lời cho mỗi kịch bản bằng **pipeline chat thật** rồi chấm hai chỉ số trên câu trả
lời đó: **Faithfulness** (mọi khẳng định có được context đã trích dẫn bảo chứng không) và **Answer Relevance**
(câu trả lời có giải quyết đúng câu hỏi không). Việc chấm hai chỉ số này SHALL dùng **LLM‑judge** vì chúng là
phán đoán ngôn ngữ không có bản deterministic đáng tin. Verdict của judge SHALL đóng khung ngắn (ví dụ
supported / partial / not‑supported cho từng khẳng định), SHALL KHÔNG để judge sinh output dài tự do.

Bộ đo SHALL báo cáo hai chỉ số **theo từng kịch bản**, không chỉ trung bình.

#### Scenario: Câu trả lời có khẳng định không nằm trong context
- **WHEN** câu trả lời sinh ra chứa một khẳng định không được insight đã trích dẫn bảo chứng
- **THEN** judge chấm khẳng định đó là not‑supported và điểm Faithfulness của kịch bản giảm tương ứng

#### Scenario: Câu trả lời lạc đề
- **WHEN** câu trả lời không giải quyết câu hỏi dù vẫn có căn cứ
- **THEN** điểm Answer Relevance của kịch bản đó thấp và được báo cáo riêng

### Requirement: Đo Citation Precision bằng cấu trúc, không gọi model

Bộ đo SHALL đo **Citation Precision** thuần bằng cấu trúc: mọi marker `[n]` trong câu trả lời SHALL trỏ tới
một insight có thật trong index đã phục vụ cho kịch bản đó, và SHALL KHÔNG có citation bịa. Phép đo này SHALL
KHÔNG gọi model.

#### Scenario: Citation trỏ tin không có trong index
- **WHEN** câu trả lời chứa một citation không khớp insight nào trong index đã phục vụ
- **THEN** Citation Precision của kịch bản đó < 1,00 và bộ đo nêu đích danh citation sai

#### Scenario: Mọi citation hợp lệ
- **WHEN** mọi marker `[n]` đều trỏ đúng insight trong index
- **THEN** Citation Precision = 1,00, đo được mà không gọi model

### Requirement: Chế độ live sinh câu trả lời, chế độ offline chấm snapshot

Bộ đo SHALL có chế độ **live** sinh câu trả lời qua pipeline chat thật (gọi model, tốn quota) và lưu snapshot,
và chế độ **offline** chấm lại trên snapshot đã lưu mà không sinh mới. Vì gọi model, bộ đo này SHALL KHÔNG chạy
trong bộ `pytest` mặc định. Tài liệu đi kèm SHALL nêu rõ chỉ chế độ live mới đo đúng pipeline hiện tại; snapshot
là câu trả lời đông lạnh, không bắt được hồi quy prompt/model.

#### Scenario: Chạy trong pytest mặc định
- **WHEN** chạy `pytest` không kèm cờ đặc biệt
- **THEN** bộ đo này KHÔNG chạy và KHÔNG phát sinh lượt gọi model nào

#### Scenario: Chấm offline không sinh mới
- **WHEN** chạy chế độ offline trên snapshot đã có
- **THEN** bộ đo chấm lại mà không gọi pipeline sinh câu trả lời, và báo cáo ghi rõ là đo trên snapshot

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

### Requirement: Bộ 50 kịch bản phủ ba mode với nhãn grounding gán tay

Bộ kịch bản SHALL gồm tối thiểu ~50 kịch bản, mỗi kịch bản ghi `mode` (`insight` / `global` / `expanded`), câu
hỏi, và tập insight đáng lẽ được trích dẫn gán tay kèm lý do. Bộ SHALL phủ cả câu hỏi kích hoạt mở rộng phạm
vi (out‑of‑scope ở chế độ per‑insight), vì đó là đường sinh câu trả lời dễ sai grounding nhất.

#### Scenario: Kịch bản mở rộng phạm vi
- **WHEN** một kịch bản hỏi câu ngoài phạm vi bài đang xem
- **THEN** bộ đo chấm câu trả lời mở rộng (`mode="expanded"`) theo cùng ba chỉ số và báo cáo riêng nhóm này

### Requirement: Hướng dẫn chạy và giới hạn diễn giải nằm cùng chỗ với code

Bộ đo SHALL đi kèm hướng dẫn chạy đặt cùng chỗ với code, nêu rõ khi nào bắt buộc chạy lại (`CHAT_SYSTEM_PROMPT`,
prompt chế độ per‑insight và sentinel mở rộng, đổi model hoặc SDK) và chi phí thật của một lần `--live`. Script
sinh phần corpus của fixture SHALL được giữ lại trong repo làm bằng chứng xuất xứ.

#### Scenario: Lập trình viên sắp sửa prompt chat
- **WHEN** một người chuẩn bị sửa prompt hệ thống hoặc prompt mode B của chat
- **THEN** tài liệu đi kèm nêu rõ phải chạy lại `--live` và ngưỡng gate phải đạt trước khi merge

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

