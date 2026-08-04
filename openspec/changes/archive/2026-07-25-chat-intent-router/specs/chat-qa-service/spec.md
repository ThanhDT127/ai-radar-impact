## ADDED Requirements

### Requirement: Định tuyến ý định trước truy vấn (fast‑path chào hỏi/meta)

Service SHALL phân loại ý định của câu hỏi bằng luật **deterministic** (không gọi model) **trước** khi nạp
insight, dựng index, hay gọi Gemini. Khi câu hỏi được nhận diện chắc chắn là chào hỏi, câu hỏi về năng lực
trợ lý (meta), hoặc lời cảm ơn, service SHALL trả một câu trả lời định sẵn tiếng Việt với `citations` rỗng
và `mode="meta"`, **KHÔNG** gọi model và **KHÔNG** dựng index.

Việc phân loại SHALL thiên về **fall‑through**: chỉ khi phần nội dung thực chất còn lại (sau khi bỏ các
token chào/meta và stopword) là **rỗng** thì mới coi là chào/meta; còn nội dung thực chất SHALL đi vào
pipeline trả lời bình thường. Service SHALL KHÔNG dùng model để phân loại ý định.

Fast‑path SHALL áp dụng bất kể có `insight_id` hay không. Câu trả lời định sẵn cho nhóm meta SHALL điều
hướng người dùng tới một truy vấn hữu ích (nêu ví dụ).

#### Scenario: Câu chào
- **WHEN** người dùng gửi "xin chào"
- **THEN** service trả câu định sẵn với `mode="meta"`, `citations` rỗng, và KHÔNG gọi Gemini

#### Scenario: Câu hỏi năng lực
- **WHEN** người dùng gửi "bạn làm được gì?"
- **THEN** service trả câu định sẵn nêu năng lực và gợi ý một truy vấn ví dụ, KHÔNG gọi Gemini

#### Scenario: Chào kèm nội dung thực chất
- **WHEN** người dùng gửi "chào, tuần này có gì cho Security?"
- **THEN** service SHALL KHÔNG fast‑path; câu hỏi chạy pipeline toàn cục và gọi model như bình thường

#### Scenario: Chào trong khi đang mở một insight
- **WHEN** người dùng gửi "chào bạn" kèm `insight_id` hợp lệ
- **THEN** service trả câu định sẵn `mode="meta"`, KHÔNG nạp bài gốc và KHÔNG gọi model

## MODIFIED Requirements

### Requirement: Endpoint chat hai chế độ
Hệ thống SHALL cung cấp endpoint `POST /api/v1/chat` nhận `{ question, history, insight_id? }` và trả về `{ answer, citations, mode }`. Trước khi chọn chế độ, service SHALL chạy định tuyến ý định: khi câu hỏi là chào hỏi/meta/cảm ơn, service SHALL trả `mode="meta"` với câu định sẵn và không gọi model. Ngược lại, khi `insight_id` có giá trị, service SHALL chạy chế độ per-insight (`mode="insight"`); khi vắng, service SHALL chạy chế độ toàn cục (`mode="global"`).

#### Scenario: Hỏi theo insight (chế độ B)
- **WHEN** client gửi câu hỏi thực chất kèm `insight_id` hợp lệ
- **THEN** service trả lời dựa trên insight đó + bài gốc từ `raw_documents.normalized_content`, với đúng 1 lượt gọi Gemini, và `mode="insight"`

#### Scenario: Hỏi toàn cục (chế độ A)
- **WHEN** client gửi câu hỏi thực chất không kèm `insight_id`
- **THEN** service dựng index từ repository và trả lời với đúng 1 lượt gọi Gemini, `mode="global"`

#### Scenario: insight_id không tồn tại
- **WHEN** client gửi câu hỏi thực chất kèm `insight_id` không có trong DB
- **THEN** service trả về lỗi 404 với error format chuẩn, không gọi Gemini

### Requirement: Budget quota riêng cho chat
Service SHALL ghi mỗi request chat vào bảng `chat_logs` (mode, `model_calls`, `citations_count`, `latency_ms`) trong khối `finally` — kể cả khi request lỗi sau khi đã gọi model. Budget dùng trong ngày SHALL tính bằng tổng `model_calls` của các bản ghi trong ngày (UTC) và so với `max_daily_chat_calls`, tách biệt với budget analysis. Hết budget SHALL trả HTTP 429 kèm thông báo tiếng Việt, và analysis pipeline không bị ảnh hưởng.

Request được fast‑path bởi định tuyến ý định (0 lượt gọi model) SHALL KHÔNG bị chặn bởi quota kể cả khi budget trong ngày đã cạn, và SHALL KHÔNG làm tăng budget đã dùng. Service MAY ghi bản ghi `chat_logs` với `model_calls=0` cho các request này để quan sát tần suất.

#### Scenario: Hết budget chat trong ngày
- **WHEN** tổng `model_calls` trong ngày đạt `max_daily_chat_calls` và người dùng gửi một câu hỏi thực chất
- **THEN** request nhận 429 với message tiếng Việt, không gọi Gemini; các job analysis vẫn chạy bình thường

#### Scenario: Chào khi đã hết budget
- **WHEN** budget trong ngày đã cạn và người dùng gửi "xin chào"
- **THEN** service vẫn trả câu định sẵn `mode="meta"`, không trả 429, và budget đã dùng không tăng

#### Scenario: Request lỗi sau khi đã gọi model
- **WHEN** lời gọi Gemini trả về thành công nhưng xử lý phía sau ném lỗi
- **THEN** bản ghi `chat_logs` vẫn được ghi với `model_calls` đã dùng, để budget không bị rò rỉ
