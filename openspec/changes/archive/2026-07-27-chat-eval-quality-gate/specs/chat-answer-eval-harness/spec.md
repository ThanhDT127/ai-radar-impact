## ADDED Requirements

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

#### Scenario: Faithfulness dưới ngưỡng
- **WHEN** Faithfulness tổng tụt dưới 0,95
- **THEN** verdict FAIL và báo cáo nêu đích danh kịch bản kéo điểm xuống

#### Scenario: Một citation bịa
- **WHEN** một kịch bản có Citation Precision < 1,00
- **THEN** verdict FAIL (ngưỡng citation là tuyệt đối)

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
