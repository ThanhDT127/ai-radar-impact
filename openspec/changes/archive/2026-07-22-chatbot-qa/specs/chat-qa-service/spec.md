# chat-qa-service

## ADDED Requirements

### Requirement: Endpoint chat hai chế độ
Hệ thống SHALL cung cấp endpoint `POST /api/v1/chat` nhận `{ question, history, insight_id? }` và trả về `{ answer, citations, mode }`. Khi `insight_id` có giá trị, service SHALL chạy chế độ per-insight (`mode="insight"`); khi vắng, service SHALL chạy chế độ toàn cục (`mode="global"`).

#### Scenario: Hỏi theo insight (chế độ B)
- **WHEN** client gửi câu hỏi kèm `insight_id` hợp lệ
- **THEN** service trả lời dựa trên insight đó + bài gốc từ `raw_documents.normalized_content`, với đúng 1 lượt gọi Gemini, và `mode="insight"`

#### Scenario: Hỏi toàn cục (chế độ A)
- **WHEN** client gửi câu hỏi không kèm `insight_id`
- **THEN** service dựng index từ repository và trả lời với đúng 1 lượt gọi Gemini, `mode="global"`

#### Scenario: insight_id không tồn tại
- **WHEN** client gửi `insight_id` không có trong DB
- **THEN** service trả về lỗi 404 với error format chuẩn, không gọi Gemini

### Requirement: Citation do server cấp phát, model không phát ra định danh
Service SHALL đánh số các insight candidate là `[1..N]` và giữ bảng ánh xạ `n → insight_id` ở phía server; prompt gửi cho model SHALL KHÔNG chứa UUID của insight. Model SHALL trả lời bằng text thuần, trích dẫn bằng marker `[n]`. Service SHALL dựng `citations` bằng cách tra marker trong bảng ánh xạ; marker ngoài phạm vi `[1..N]` SHALL bị bỏ khỏi câu trả lời nhưng phần còn lại của câu trả lời SHALL được giữ.

#### Scenario: Câu hỏi có dữ liệu trả lời
- **WHEN** câu hỏi khớp với insight trong hệ thống
- **THEN** answer chứa marker `[n]`, và `citations` được service dựng đầy đủ (`insight_id`, `title`, `source_url`) từ bảng ánh xạ

#### Scenario: Model trích dẫn marker ngoài phạm vi
- **WHEN** model trả về `[99]` trong khi chỉ có 40 candidate
- **THEN** service bỏ marker đó khỏi answer, giữ nguyên phần nội dung còn lại, và không tạo citation tương ứng

#### Scenario: Câu trả lời khẳng định nhưng không có marker nào
- **WHEN** model trả lời mang tính khẳng định mà không có bất kỳ marker `[n]` nào và cũng không phải dạng "không tìm thấy"
- **THEN** service thay câu trả lời bằng thông báo không đủ căn cứ (fail-closed)

#### Scenario: Không tìm thấy dữ liệu
- **WHEN** câu hỏi không khớp insight nào trong index
- **THEN** service trả lời rõ ràng rằng không tìm thấy thông tin trong hệ thống, không suy diễn từ kiến thức ngoài, `citations` rỗng, và câu trả lời KHÔNG bị fail-closed chặn

### Requirement: Chat không dùng structured output
Lời gọi Gemini cho chat SHALL KHÔNG đặt `response_mime_type="application/json"` và SHALL KHÔNG khai báo `response_schema`; câu trả lời SHALL là text thuần.

#### Scenario: Câu trả lời dài
- **WHEN** model sinh câu trả lời dài chạm `max_output_tokens`
- **THEN** phần đã sinh vẫn dùng được (bị cắt cuối câu), không có lỗi parse JSON làm hỏng toàn bộ request

### Requirement: Chế độ per-insight dùng bài gốc đầy đủ
Ở chế độ B, context gửi cho Gemini SHALL gồm các trường insight (`title`, `signal`, `so_what`, `why_it_matters`, `recommendations`, `risks`, `summary_medium`) và toàn bộ `raw_documents.normalized_content` của bài gốc (nội dung đã bị giới hạn 8000 ký tự từ lúc ingest nên không cần cắt thêm).

#### Scenario: Hỏi chi tiết nằm ngoài summary
- **WHEN** người dùng hỏi một chi tiết có trong bài gốc nhưng không có trong summary/signal của insight
- **THEN** bot trả lời được dựa trên bài gốc

#### Scenario: Bài gốc đã bị tombstone-purge
- **WHEN** insight còn tồn tại nhưng `normalized_content` của tài liệu gốc đã bị xoá theo retention
- **THEN** service trả lời bằng các trường insight và nói rõ rằng bài gốc đã hết hạn lưu trữ, không trả lời như thể vẫn còn bài

### Requirement: Retrieval toàn cục do server điều khiển
Ở chế độ A, service SHALL tự lọc và xếp hạng candidate rồi dựng index nén trước khi gọi model; service SHALL KHÔNG dùng function-calling và SHALL KHÔNG để model chọn điều kiện truy vấn. Bộ lọc SHALL luôn gồm `status = "published"` và `is_primary = true`, cộng cửa sổ thời gian theo `chat_window_days` (0 = không giới hạn). Mỗi câu hỏi SHALL dùng tối đa 2 lượt gọi model.

#### Scenario: Câu hỏi có điều kiện lọc
- **WHEN** người dùng hỏi "tuần này có tin bảo mật nào cho Security không?"
- **THEN** service dựng index từ cửa sổ thời gian đã cấu hình và model trả lời từ metadata role/topic/ngày có sẵn trong index, với 1 lượt gọi

### Requirement: Xếp hạng hai tầng — liên quan trước, quan trọng sau
Xếp hạng candidate SHALL dùng khoá hai tầng: (1) **độ liên quan** giữa từ khoá câu hỏi và nội dung tin, (2) **độ quan trọng** qua `delivery_engine.score_for_role()`. Khi câu hỏi không chứa từ khoá đặc trưng nào, tầng (1) SHALL hoà và thứ tự SHALL rơi về tầng (2). Việc tách từ khoá SHALL nhận từ dài từ **2 ký tự** trở lên (tiếng Việt đơn âm), lọc nhiễu bằng danh sách stopword chứ không bằng độ dài.

#### Scenario: Tin đúng chủ đề nhưng độ khẩn thấp
- **WHEN** người dùng hỏi về một chủ đề ngách mà các tin liên quan đều có `recommendations[role].urgency` thấp, trong khi hệ thống có tin khẩn thuộc chủ đề khác
- **THEN** tin đúng chủ đề SHALL xếp trên tin khẩn lạc đề, và SHALL nằm trong index kể cả khi có trần top-K

#### Scenario: Câu hỏi chung chung
- **WHEN** người dùng hỏi "có gì mới không?" (không từ khoá đặc trưng)
- **THEN** thứ tự index theo `score_for_role()`, tin quan trọng nhất lên đầu

### Requirement: Trần top-K cho index
Service SHALL cắt index ở `chat_index_top_k` tin **sau khi xếp hạng** (0 = không giới hạn). Khi có tin bị cắt, prompt SHALL cho model biết tổng số tin thực tế khớp để con số "còn N tin khác" không bị thiếu. Việc xác định "vai trò không có tin nào" SHALL tính trên **toàn bộ tập khớp trước khi cắt**.

#### Scenario: Index bị cắt
- **WHEN** số tin khớp vượt `chat_index_top_k`
- **THEN** index chỉ chứa top-K tin, và prompt nêu rõ tổng số tin thực tế khớp

#### Scenario: Vai trò có tin nhưng xếp dưới ngưỡng cắt
- **WHEN** người dùng hỏi về một vai trò mà mọi tin của vai trò đó đều xếp hạng dưới `chat_index_top_k`
- **THEN** service SHALL KHÔNG báo "chưa có tin nào cho vai trò này"

#### Scenario: Xếp hạng thay vì lọc ngưỡng
- **WHEN** người dùng hỏi theo một vai trò mà mọi insight đều có `recommendations[role].urgency = "medium"` (ví dụ Data Scientist)
- **THEN** index vẫn chứa các tin liên quan, xếp theo tuple đa tiêu chí của `score_for_role`, không bị loại sạch vì không đạt ngưỡng urgency

#### Scenario: Vai trò chưa có dữ liệu
- **WHEN** người dùng hỏi về một vai trò không xuất hiện trong bất kỳ insight nào (ví dụ Data Analyst)
- **THEN** bot nói rõ chưa có tin nào cho vai trò đó thay vì im lặng hoặc trả lời chung chung

### Requirement: Budget quota riêng cho chat
Service SHALL ghi mỗi request chat vào bảng `chat_logs` (mode, `model_calls`, `citations_count`, `latency_ms`) trong khối `finally` — kể cả khi request lỗi sau khi đã gọi model. Budget dùng trong ngày SHALL tính bằng tổng `model_calls` của các bản ghi trong ngày (UTC) và so với `max_daily_chat_calls`, tách biệt với budget analysis. Hết budget SHALL trả HTTP 429 kèm thông báo tiếng Việt, và analysis pipeline không bị ảnh hưởng.

#### Scenario: Hết budget chat trong ngày
- **WHEN** tổng `model_calls` trong ngày đạt `max_daily_chat_calls`
- **THEN** request chat tiếp theo nhận 429 với message tiếng Việt, không gọi Gemini; các job analysis vẫn chạy bình thường

#### Scenario: Request lỗi sau khi đã gọi model
- **WHEN** lời gọi Gemini trả về thành công nhưng xử lý phía sau ném lỗi
- **THEN** bản ghi `chat_logs` vẫn được ghi với `model_calls` đã dùng, để budget không bị rò rỉ

### Requirement: Chat không chặn event loop
Lời gọi Gemini của chat SHALL được thực thi ngoài event loop (`asyncio.to_thread` hoặc tương đương). Client Gemini dùng cho chat SHALL là singleton dùng chung, KHÔNG khởi tạo mới theo từng request.

#### Scenario: Request khác chạy song song
- **WHEN** một câu hỏi chat đang chờ Gemini trả lời
- **THEN** các request API khác (danh sách insight, stats) vẫn được phục vụ bình thường trong thời gian đó

### Requirement: Trả lời tiếng Việt, hỗ trợ hội thoại đa lượt
Câu trả lời SHALL bằng tiếng Việt (technical terms giữ tiếng Anh). Service SHALL nhận `history` (tối đa 10 lượt gần nhất) để hiểu câu hỏi nối tiếp; history do client giữ, service SHALL KHÔNG lưu trạng thái hội thoại.

#### Scenario: Câu hỏi nối tiếp
- **WHEN** người dùng đã hỏi về một insight và nhắn tiếp "còn rủi ro thì sao?" kèm history
- **THEN** bot hiểu "rủi ro" tham chiếu insight đang bàn và trả lời đúng ngữ cảnh

#### Scenario: History vượt 10 lượt
- **WHEN** client gửi history dài hơn 10 lượt
- **THEN** service chỉ dùng 10 lượt gần nhất
