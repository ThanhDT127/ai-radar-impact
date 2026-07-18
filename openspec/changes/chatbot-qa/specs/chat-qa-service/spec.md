# chat-qa-service

## ADDED Requirements

### Requirement: Endpoint chat hai chế độ
Hệ thống SHALL cung cấp endpoint `POST /api/v1/chat` nhận `{ question, history, insight_id? }` và trả về `{ answer, citations, mode }`. Khi `insight_id` có giá trị, service SHALL chạy chế độ per-insight (`mode="insight"`); khi vắng, service SHALL chạy chế độ toàn cục (`mode="global"`).

#### Scenario: Hỏi theo insight (chế độ B)
- **WHEN** client gửi câu hỏi kèm `insight_id` hợp lệ
- **THEN** service trả lời dựa trên insight đó + full text bài gốc từ `raw_documents`, với đúng 1 lượt gọi Gemini, và `mode="insight"`

#### Scenario: Hỏi toàn cục (chế độ A)
- **WHEN** client gửi câu hỏi không kèm `insight_id`
- **THEN** service dùng Gemini function-calling với tool `search_insights` để truy vấn repository và tổng hợp câu trả lời, `mode="global"`

#### Scenario: insight_id không tồn tại
- **WHEN** client gửi `insight_id` không có trong DB
- **THEN** service trả về lỗi 404 với error format chuẩn, không gọi Gemini

### Requirement: Trả lời grounded kèm citation
Mọi câu trả lời có nội dung khẳng định SHALL kèm ít nhất 1 citation trỏ về insight nguồn (`insight_id`, `title`, `source_url`). Service SHALL loại bỏ citation id không tồn tại trong DB. Câu trả lời không có citation hợp lệ và không thuộc dạng "không tìm thấy" SHALL bị chặn và thay bằng thông báo không đủ căn cứ.

#### Scenario: Câu hỏi có dữ liệu trả lời
- **WHEN** câu hỏi khớp với insight trong hệ thống
- **THEN** answer kèm danh sách citations đã được resolve từ DB (id tồn tại, có title + source_url)

#### Scenario: Không tìm thấy dữ liệu
- **WHEN** câu hỏi không khớp insight nào (tool trả về rỗng)
- **THEN** service trả lời rõ ràng rằng không tìm thấy thông tin trong hệ thống, không suy diễn từ kiến thức ngoài, citations rỗng

#### Scenario: Model bịa citation id
- **WHEN** Gemini trả về citation_id không tồn tại trong DB
- **THEN** service loại id đó khỏi citations; nếu không còn citation nào hợp lệ, answer bị thay bằng thông báo không đủ căn cứ

### Requirement: Chế độ per-insight dùng full text bài gốc
Ở chế độ B, context gửi cho Gemini SHALL gồm các trường insight (`title`, `signal`, `why_it_matters`, `recommendations`, `risks`, `summary_medium`) và nội dung `raw_documents.content` của bài gốc, cắt tối đa 30.000 ký tự.

#### Scenario: Hỏi chi tiết nằm ngoài summary
- **WHEN** người dùng hỏi một chi tiết có trong bài gốc nhưng không có trong summary/signal của insight
- **THEN** bot trả lời được dựa trên full text bài gốc

### Requirement: Retrieval toàn cục qua function-calling có trần lượt gọi
Ở chế độ A, service SHALL khai báo tool `search_insights(keyword?, role?, topic?, urgency?, days_back?, limit)` và `get_insight(insight_id)` map vào `InsightRepository`. Số lượt gọi model cho một câu hỏi SHALL không vượt quá 4; chạm trần thì tổng hợp câu trả lời từ dữ liệu đã thu được.

#### Scenario: Câu hỏi có điều kiện lọc
- **WHEN** người dùng hỏi "tuần này có tin bảo mật nào cho Engineering không?"
- **THEN** model gọi `search_insights` với filter tương ứng (role, topic/urgency, days_back=7) và trả lời từ kết quả

#### Scenario: Chạm trần tool loop
- **WHEN** hội thoại function-calling đạt 4 lượt gọi model mà model vẫn muốn gọi tool tiếp
- **THEN** service dừng vòng lặp và yêu cầu model trả lời với dữ liệu hiện có

### Requirement: Budget quota riêng cho chat
Service SHALL đếm mọi lượt gọi Gemini của chat (kể cả các lượt trong tool loop) vào budget riêng `max_daily_chat_calls`, tách biệt với budget analysis. Hết budget SHALL trả HTTP 429 kèm thông báo tiếng Việt, và analysis pipeline không bị ảnh hưởng.

#### Scenario: Hết budget chat trong ngày
- **WHEN** tổng lượt gọi chat trong ngày đạt `max_daily_chat_calls`
- **THEN** request chat tiếp theo nhận 429 với message tiếng Việt; các job analysis vẫn chạy bình thường

### Requirement: Trả lời tiếng Việt, hỗ trợ hội thoại đa lượt
Câu trả lời SHALL bằng tiếng Việt (technical terms giữ tiếng Anh). Service SHALL nhận `history` (tối đa 10 lượt gần nhất) để hiểu câu hỏi nối tiếp.

#### Scenario: Câu hỏi nối tiếp
- **WHEN** người dùng đã hỏi về một insight và nhắn tiếp "còn rủi ro thì sao?" kèm history
- **THEN** bot hiểu "rủi ro" tham chiếu insight đang bàn và trả lời đúng ngữ cảnh
