# gate-eval-harness Specification

## Purpose
TBD - created by archiving change gate-benchmark-durability. Update Purpose after archive.
## Requirements
### Requirement: Benchmark gate tự chứa, không phụ thuộc dữ liệu sống

Bộ đo tiêu chí gate SHALL lưu đủ đầu vào để tái lập trong repo: mỗi mẫu gồm `doc_id`, `source`,
`source_type`, `title`, nội dung cắt đúng bằng cửa sổ mà `build_gate_prompt` đọc, nhãn tay
(`human_label`) và lý do chấm (`human_reason`). Bộ đo SHALL chạy được khi `raw_documents` tương ứng đã
bị tombstone-purge hoặc xoá.

#### Scenario: Chạy benchmark sau khi dữ liệu gốc đã bị purge
- **WHEN** 54 `raw_documents` của mẫu đã bị `purge_expired` xoá `normalized_content`
- **THEN** benchmark vẫn chạy được và sinh confusion matrix từ fixture trong repo, không truy vấn DB

#### Scenario: Cửa sổ nội dung khớp cửa sổ gate thật
- **WHEN** benchmark khởi động
- **THEN** nó kiểm tra độ dài cắt của fixture khớp hằng số cắt trong `build_gate_prompt`
- **AND** nếu lệch thì dừng với thông báo rõ ràng thay vì đo trên đầu vào sai lệch

### Requirement: Hai chế độ chạy — offline mặc định, gọi model khi được yêu cầu

Bộ đo SHALL mặc định chạy **offline**: đối chiếu nhãn tay với verdict đã lưu, không gọi Vertex AI và
không tốn quota. Bộ đo SHALL có chế độ gọi model thật để đo lại verdict trên `GATE_PROMPT` hiện hành.

#### Scenario: Chạy offline
- **WHEN** người dùng chạy benchmark không kèm cờ gọi model
- **THEN** benchmark in confusion matrix từ verdict đã lưu và không phát sinh lần gọi Gemini nào

#### Scenario: Chạy đo lại thật
- **WHEN** người dùng chạy benchmark kèm cờ gọi model
- **THEN** benchmark chạy `gate_analyze` trên từng fixture với `temperature=0.0`
- **AND** in confusion matrix mới cùng phần chênh lệch so với matrix baseline đã lưu

#### Scenario: Không chạy tự động trong CI
- **WHEN** chạy `pytest` mặc định
- **THEN** phần gọi model thật bị bỏ qua (skip), chỉ phần kiểm tra tính toàn vẹn fixture được chạy

### Requirement: Kết quả đo đối chiếu được với baseline đã chốt

Bộ đo SHALL sinh confusion matrix theo quy ước đã dùng ở `w4-gate-accuracy` (SIGNAL = positive, gate
PASS = predicted positive; TP/FP/FN/TN) kèm accuracy, precision, recall, F1, và bảng theo `source_type`.
Bộ đo SHALL giữ nguyên 54 nhãn tay gốc, không gán nhãn lại.

#### Scenario: Tái lập kết quả đã chốt
- **WHEN** chạy chế độ gọi model thật trên `GATE_PROMPT` không thay đổi
- **THEN** kết quả khớp bảng đã chốt ngày 21/07/2026 (accuracy 94%, recall 100%, precision 92%)
- **AND** nếu không khớp, benchmark báo rõ phần lệch để điều tra trước khi coi là baseline mới

#### Scenario: Phát hiện hồi quy sau khi sửa prompt
- **WHEN** `GATE_PROMPT` bị sửa và benchmark chạy lại ở chế độ gọi model thật
- **THEN** báo cáo nêu rõ mẫu nào đổi verdict, theo chiều nào (SIGNAL bị loại thêm / NOISE lọt thêm)

### Requirement: Hướng dẫn chạy lại phải đúng và tự đủ

Bộ đo SHALL đi kèm hướng dẫn chạy nằm cùng chỗ với code, nêu lệnh chạy chính xác, chi phí ước tính của
chế độ gọi model thật, và giới hạn diễn giải của mẫu. Tài liệu SHALL không hướng người đọc tới nguồn
không tồn tại.

#### Scenario: Người chưa từng chạy benchmark làm theo hướng dẫn
- **WHEN** một người mở hướng dẫn và làm theo từng bước
- **THEN** benchmark chạy được mà không cần khôi phục file từ lịch sử git, không cần hỏi thêm ai

#### Scenario: Runbook cũ trong archive
- **WHEN** người đọc mở `measurement.md` của `w4-gate-accuracy`
- **THEN** nó trỏ tới harness hiện hành bằng đường dẫn đúng sau khi change đã archive
- **AND** không còn câu hướng dẫn khôi phục `eval_gate.py` từ git history

