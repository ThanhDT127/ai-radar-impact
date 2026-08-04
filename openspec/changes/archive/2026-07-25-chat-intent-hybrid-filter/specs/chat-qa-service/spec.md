## MODIFIED Requirements

### Requirement: Định tuyến ý định trước truy vấn (fast‑path chào hỏi/meta)

Service SHALL phân loại ý định của câu hỏi **trước** khi nạp insight, dựng index, hay gọi model trả lời.
Khi câu hỏi được nhận diện là chào hỏi, câu hỏi về năng lực trợ lý (meta), hoặc lời cảm ơn, service SHALL
trả một câu trả lời định sẵn tiếng Việt với `citations` rỗng và `mode="meta"`, **KHÔNG** gọi model trả lời
và **KHÔNG** dựng index.

Việc phân loại SHALL theo **hai tầng**:

1. **Tầng 1 — luật tất định, không gọi model.** Tầng này SHALL trả một trong ba trạng thái: nhóm ý định,
   "câu tra cứu", hoặc "lưỡng lự". Tầng 1 SHALL quyết dứt điểm mọi ca mà luật diễn đạt được chính xác.
2. **Tầng 2 — model nhẹ.** Service SHALL gọi model phân loại **chỉ khi** tầng 1 trả "lưỡng lự". Model này
   SHALL khác model trả lời và SHALL được cấu hình cho độ trễ thấp nhất (nhãn một ký tự, trần output ≤ 4
   token, `temperature=0`, không retry).

Service SHALL KHÔNG gọi tầng 2 cho câu mà tầng 1 đã quyết được. Câu chứa **đại từ hồi chỉ** (trỏ về bài
đang xem) mà KHÔNG kèm từ tự quy chiếu về trợ lý SHALL được tầng 1 phân loại là câu tra cứu, KHÔNG nhường
cho tầng 2.

Phân loại SHALL thiên về **fall‑through**: mọi lỗi, timeout, hay nhãn không hợp lệ của tầng 2 SHALL rơi về
pipeline trả lời bình thường. Khi tầng 2 bị tắt bằng cấu hình, ca "lưỡng lự" SHALL rơi về pipeline.

Lượt gọi tầng 2 SHALL KHÔNG được tính vào bộ đếm quota của lượt gọi trả lời.

Fast‑path SHALL áp dụng bất kể có `insight_id` hay không. Câu trả lời định sẵn cho nhóm meta SHALL điều
hướng người dùng tới một truy vấn hữu ích (nêu ví dụ).

#### Scenario: Câu chào
- **WHEN** người dùng gửi "xin chào"
- **THEN** tầng 1 quyết ngay, service trả câu định sẵn với `mode="meta"`, `citations` rỗng, và KHÔNG gọi model nào

#### Scenario: Câu hỏi năng lực có tự quy chiếu
- **WHEN** người dùng gửi "bạn làm được gì?"
- **THEN** tầng 1 quyết ngay, service trả câu định sẵn nêu năng lực và gợi ý một truy vấn ví dụ, KHÔNG gọi model nào

#### Scenario: Chào kèm nội dung thực chất
- **WHEN** người dùng gửi "chào, tuần này có gì cho Security?"
- **THEN** tầng 1 quyết đây là câu tra cứu; service SHALL KHÔNG fast‑path và SHALL KHÔNG gọi tầng 2

#### Scenario: Đại từ hồi chỉ không kèm tự quy chiếu
- **WHEN** người dùng gửi "nó là ai" hoặc "công cụ này hỗ trợ gì"
- **THEN** tầng 1 phân loại là câu tra cứu (đang hỏi về thứ nói trong bài), KHÔNG gọi tầng 2, KHÔNG trả preset

#### Scenario: Câu lưỡng lự được nhường cho model nhẹ
- **WHEN** người dùng gửi "bot này dùng để làm gì" — có tự quy chiếu nhưng còn token ngoài tập cụm năng lực
- **THEN** tầng 1 trả "lưỡng lự"; service gọi model phân loại nhẹ và dùng kết quả của nó

#### Scenario: Tầng 2 lỗi
- **WHEN** tầng 1 trả "lưỡng lự" và lời gọi model phân loại ném lỗi hoặc trả nhãn không hợp lệ
- **THEN** service SHALL KHÔNG ném lỗi ra ngoài; câu hỏi chạy pipeline trả lời bình thường

#### Scenario: Tầng 2 bị tắt bằng cấu hình
- **WHEN** `INTENT_CLASSIFIER_ENABLED=false` và người dùng gửi một câu lưỡng lự
- **THEN** service SHALL KHÔNG gọi model phân loại; câu hỏi chạy pipeline trả lời bình thường

#### Scenario: Chào trong khi đang mở một insight
- **WHEN** người dùng gửi "chào bạn" kèm `insight_id` hợp lệ
- **THEN** service trả preset, KHÔNG nạp bài gốc, KHÔNG gọi model nào

#### Scenario: Fast‑path khi quota đã cạn
- **WHEN** `SUM(chat_logs.model_calls)` trong ngày đã chạm `max_daily_chat_calls` và người dùng gửi "xin chào"
- **THEN** service vẫn trả preset (không 429), và bản ghi `chat_logs` có `model_calls=0`

#### Scenario: Lượt phân loại không đội quota trả lời
- **WHEN** một câu được fast‑path nhờ tầng 2
- **THEN** bản ghi `chat_logs` có `model_calls=0` — lượt gọi phân loại không cộng vào bộ đếm quota
