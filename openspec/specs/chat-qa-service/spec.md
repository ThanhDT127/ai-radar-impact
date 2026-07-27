# chat-qa-service

## Purpose

Cho phép người dùng hỏi sâu vào kho insight thay vì chỉ đọc-lướt dashboard: một endpoint chat hai chế
độ (hỏi trong phạm vi một insight, hoặc hỏi toàn cục), grounded trên dữ liệu đã curate. Retrieval do
**server** điều khiển (lọc → xếp hạng → dựng index nén), model chỉ nhận context đã dựng sẵn và trả
text thuần có marker `[n]`; citation do server cấp phát nên model không có gì để bịa.

Chat là consumer Gemini thứ hai, có budget riêng tách khỏi analysis pipeline. Phần giao diện nằm ở
capability `chat-web-widget`.
## Requirements
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

### Requirement: Chat không dùng structured output
Lời gọi Gemini cho chat SHALL KHÔNG đặt `response_mime_type="application/json"` và SHALL KHÔNG khai báo `response_schema`; câu trả lời SHALL là text thuần.

#### Scenario: Câu trả lời dài
- **WHEN** model sinh câu trả lời dài chạm `max_output_tokens`
- **THEN** không có lỗi parse JSON làm hỏng toàn bộ request; phần đã sinh SHALL được xử lý theo yêu cầu "Câu trả lời chat không bao giờ dở dang" (hỏi lại, rồi cắt về ranh giới câu) thay vì trả thẳng cho client

### Requirement: Chế độ per-insight dùng bài gốc đầy đủ
Ở chế độ B, context gửi cho Gemini SHALL gồm các trường insight (`title`, `signal`, `so_what`, `why_it_matters`, `recommendations`, `risks`, `summary_medium`) và toàn bộ `raw_documents.normalized_content` của bài gốc (nội dung đã bị giới hạn 8000 ký tự từ lúc ingest nên không cần cắt thêm).

Khi câu hỏi không thể trả lời từ nội dung bài, service SHALL KHÔNG trả lời cụt mà SHALL mở rộng sang toàn hệ thống theo requirement "Auto‑fallback từ scope bài sang scope mở rộng". Chế độ B chỉ trả lời trong phạm vi bài khi câu hỏi thực sự nằm trong phạm vi đó.

#### Scenario: Hỏi chi tiết nằm ngoài summary
- **WHEN** người dùng hỏi một chi tiết có trong bài gốc nhưng không có trong summary/signal của insight
- **THEN** bot trả lời được dựa trên bài gốc, không mở rộng

#### Scenario: Bài gốc đã bị tombstone-purge
- **WHEN** insight còn tồn tại nhưng `normalized_content` của tài liệu gốc đã bị xoá theo retention
- **THEN** service trả lời bằng các trường insight và nói rõ rằng bài gốc đã hết hạn lưu trữ, không trả lời như thể vẫn còn bài

#### Scenario: Câu hỏi vượt phạm vi bài kích hoạt mở rộng
- **WHEN** người dùng đang mở một insight nhưng hỏi câu mà nội dung bài không đề cập
- **THEN** service mở rộng sang toàn hệ thống thay vì trả lời "bài này không đề cập" rồi dừng

### Requirement: Retrieval toàn cục do server điều khiển
Ở chế độ A, service SHALL tự lọc và xếp hạng candidate rồi dựng index nén trước khi gọi model; service SHALL KHÔNG dùng function-calling và SHALL KHÔNG để model chọn điều kiện truy vấn. Bộ lọc SHALL luôn gồm `status = "published"` và `is_primary = true`, cộng cửa sổ thời gian theo `chat_window_days` (0 = không giới hạn). Mỗi câu hỏi SHALL dùng tối đa 2 lượt gọi model.

#### Scenario: Câu hỏi có điều kiện lọc
- **WHEN** người dùng hỏi "tuần này có tin bảo mật nào cho Security không?"
- **THEN** service dựng index từ cửa sổ thời gian đã cấu hình và model trả lời từ metadata role/topic/ngày có sẵn trong index, với 1 lượt gọi

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

### Requirement: Câu trả lời chat không bao giờ dở dang

Service SHALL KHÔNG trả về client một câu trả lời bị cắt giữa chừng. Khi lời gọi model kết thúc vì chạm
`max_output_tokens`, service SHALL gọi lại model **một lần** với chỉ dẫn ràng buộc **độ dài trình bày**
(gộp ý, giới hạn số gạch đầu dòng) — chỉ dẫn này SHALL yêu cầu câu trả lời phủ **đủ ý** đã hỏi và SHALL
KHÔNG thu hẹp phạm vi câu hỏi. Câu hỏi của người dùng SHALL được truyền lại nguyên văn.

Nếu lượt hỏi lại vẫn bị cắt, service SHALL cắt câu trả lời về **ranh giới câu hoàn chỉnh cuối cùng**.
Service SHALL KHÔNG nối thêm ghi chú xin lỗi hay hướng dẫn người dùng hỏi lại vào nội dung câu trả lời.

Lượt hỏi lại SHALL được tính vào số lượt gọi model trả về cho tầng gọi, để bộ đếm budget khớp với số lượt
thực sự tốn tiền.

#### Scenario: Lượt đầu trọn vẹn
- **WHEN** model trả lời và không chạm trần output
- **THEN** service trả nguyên văn câu trả lời và SHALL KHÔNG gọi lại model

#### Scenario: Lượt đầu bị cắt, hỏi lại thành công
- **WHEN** lượt đầu kết thúc vì `MAX_TOKENS` và lượt hỏi lại trả về câu trả lời trọn vẹn
- **THEN** service trả câu trả lời của **lượt hỏi lại**, và báo về 2 lượt gọi đã tốn tiền

#### Scenario: Hỏi lại vẫn bị cắt
- **WHEN** cả lượt đầu lẫn lượt hỏi lại đều kết thúc vì `MAX_TOKENS`
- **THEN** service cắt về câu hoàn chỉnh cuối cùng và trả về, KHÔNG kèm ghi chú nào về việc bị cắt

#### Scenario: Không bao giờ lộ ghi chú cắt ngắn
- **WHEN** bất kỳ nhánh nào của luồng trả lời hoàn tất
- **THEN** nội dung trả về SHALL KHÔNG chứa ghi chú kiểu "câu trả lời bị cắt vì quá dài" hay lời khuyên "hỏi hẹp hơn"

#### Scenario: Lượt hỏi lại mang ràng buộc độ dài
- **WHEN** service gọi lại model sau khi bị cắt
- **THEN** `system_instruction` của lượt đó chứa ràng buộc độ dài, còn nội dung câu hỏi giữ nguyên như lượt đầu

### Requirement: Auto‑fallback từ scope bài sang scope mở rộng

Ở chế độ per‑insight, khi câu hỏi rõ ràng **không thể trả lời từ nội dung bài đang xem**, service SHALL tự
mở rộng phạm vi sang toàn hệ thống thay vì trả lời cụt. Cơ chế: lượt gọi model ở chế độ per‑insight SHALL
được hướng dẫn phát một **sentinel văn bản thuần đã định nghĩa** khi (và chỉ khi) câu hỏi nằm ngoài phạm vi
bài; service phát hiện sentinel SHALL dựng **context mở rộng** gồm insight của bài đang xem **cộng** index
toàn cục đã xếp hạng (tái dùng đúng retrieval do server điều khiển của chế độ toàn cục), rồi gọi model **lần
thứ hai** để trả lời.

Câu trả lời mở rộng SHALL nêu rõ rằng đã tìm trên toàn hệ thống (không chỉ bài đang xem), citation SHALL lấy
từ bảng ánh xạ `[n]` của index toàn cục, và `mode` SHALL là `"expanded"`. Tổng số **bước trả lời** cho một câu hỏi
SHALL KHÔNG vượt quá 2. Một bước MAY tiêu nhiều hơn một lượt gọi tính tiền khi câu trả lời bị
cắt và phải hỏi lại; trần áp lên số bước, còn bộ đếm budget SHALL ghi số lượt thực đã tốn tiền. Service SHALL KHÔNG dùng `response_schema` để phát/đọc sentinel. Sentinel SHALL
được phát **dè dặt**: câu hỏi còn trả lời được dù chỉ một phần từ nội dung bài SHALL KHÔNG kích hoạt mở rộng.

Service SHALL KHÔNG dùng một lượt gọi model riêng chỉ để phân loại phạm vi; tín hiệu ngoài‑phạm‑vi SHALL là
kết quả của chính lượt gọi trả lời per‑insight.

#### Scenario: Câu hỏi nằm trong phạm vi bài
- **WHEN** người dùng đang mở một insight và hỏi một câu trả lời được từ nội dung bài
- **THEN** service trả lời ở chế độ per‑insight với đúng 1 lượt gọi model, `mode="insight"`, không mở rộng

#### Scenario: Câu hỏi vượt phạm vi bài
- **WHEN** người dùng đang mở insight B và hỏi về một chủ đề chỉ có ở insight khác trong hệ thống
- **THEN** lượt gọi per‑insight phát sentinel, service dựng context mở rộng (insight B + index toàn cục) và gọi model lần hai
- **AND** câu trả lời nêu rõ đã tìm toàn hệ thống, `citations` lấy từ index toàn cục, `mode="expanded"`, tổng 2 lượt gọi

#### Scenario: Mở rộng nhưng toàn hệ thống cũng không có
- **WHEN** câu hỏi vượt phạm vi bài và index toàn cục cũng không có tin nào khớp
- **THEN** service trả lời trung thực rằng không tìm thấy trong toàn hệ thống, `citations` rỗng, không bịa từ bài đang xem

#### Scenario: Trần hai bước trả lời
- **WHEN** một câu hỏi kích hoạt mở rộng
- **THEN** service dùng đúng 2 bước (per‑insight + toàn cục) và SHALL KHÔNG thực hiện bước thứ ba; khi không bước nào bị cắt, `chat_logs` ghi `model_calls=2`

#### Scenario: Một bước phải hỏi lại vì câu trả lời bị cắt
- **WHEN** một câu hỏi kích hoạt mở rộng và một trong hai bước bị cắt nên phải hỏi lại
- **THEN** service vẫn hoàn tất đủ hai bước (KHÔNG lỗi vì chạm trần) và `chat_logs` ghi đúng số lượt đã tốn tiền, lớn hơn 2

#### Scenario: Sentinel phát dè dặt
- **WHEN** câu hỏi trả lời được một phần từ nội dung bài
- **THEN** lượt gọi per‑insight SHALL trả lời trực tiếp và SHALL KHÔNG phát sentinel, không phát sinh lượt gọi mở rộng

### Requirement: Trục xếp hạng theo vai trò nhận diện vai trò theo biên từ

Khi câu hỏi nêu tên một vai trò trong `ALLOWED_ROLES`, tầng độ quan trọng SHALL xếp hạng theo trục vai trò
đó thay vì theo `affected_roles` của từng tin. Việc nhận diện tên vai trò trong câu hỏi SHALL khớp **theo
biên từ**: tên vai trò được tách thành dãy token bằng cùng quy tắc tách token dùng cho từ khoá, và SHALL
chỉ tính là khớp khi dãy token đó xuất hiện **liên tiếp và trọn vẹn** trong dãy token của câu hỏi.

Service SHALL KHÔNG suy ra vai trò từ chuỗi con nằm bên trong một từ khác. Service SHALL ghi log mức DEBUG
trục xếp hạng đã chọn cho mỗi câu hỏi ở chế độ toàn cục.

*Ghi chú:* yêu cầu này chi phối cả việc tính danh sách vai trò không có tin nào ảnh hưởng tới — nhận diện
sai vai trò dẫn tới tuyên bố sai về khoảng trống dữ liệu.

#### Scenario: Tên vai trò là chuỗi con của một từ khác
- **WHEN** người dùng hỏi "tin về device IoT mới"
- **THEN** service SHALL KHÔNG nhận diện vai trò `Dev`
- **AND** thứ tự xếp hạng rơi về mức quan trọng cao nhất trên `affected_roles` của từng tin

#### Scenario: Từ thuộc taxonomy khác chứa tên vai trò
- **WHEN** người dùng hỏi "DevOps cần chú ý gì"
- **THEN** service SHALL KHÔNG nhận diện vai trò `Dev` (`DevOps` thuộc taxonomy `Source.target_roles`,
  không thuộc `ALLOWED_ROLES`)

#### Scenario: Tên vai trò một từ đứng riêng
- **WHEN** người dùng hỏi "Dev cần làm gì tuần này"
- **THEN** service SHALL nhận diện vai trò `Dev` và xếp hạng theo trục đó

#### Scenario: Tên vai trò gồm nhiều từ
- **WHEN** người dùng hỏi câu chứa "Data Analyst" hoặc "Người dùng phổ thông"
- **THEN** service SHALL nhận diện đúng vai trò đó, khớp trọn cụm nhiều từ

#### Scenario: Câu hỏi không nêu vai trò nào
- **WHEN** người dùng hỏi "có gì mới không"
- **THEN** service SHALL KHÔNG chọn trục vai trò nào
- **AND** xếp hạng theo mức quan trọng cao nhất trên `affected_roles` của từng tin, mặc định `Toàn công ty`
  khi tin không có vai trò nào

#### Scenario: Ghi lại trục đã chọn
- **WHEN** service xử lý một câu hỏi ở chế độ toàn cục
- **THEN** service ghi log mức DEBUG nêu vai trò được nhận diện (hoặc việc không nhận diện được vai trò nào)

### Requirement: Endpoint streaming với sự kiện tiến trình và grounding cuối luồng

Hệ thống SHALL cung cấp endpoint `POST /api/v1/chat/stream` nhận cùng payload `{ question, history, insight_id? }`
và trả về luồng **Server‑Sent Events**. Luồng SHALL phát: **sự kiện tiến trình** (status) mô tả giai đoạn
pipeline, **sự kiện token** mang từng phần câu trả lời khi model sinh, và **một sự kiện chốt** ở cuối. Endpoint
blocking `POST /api/v1/chat` SHALL được giữ nguyên hành vi.

Fail‑closed và citation SHALL được áp trên câu trả lời **hoàn chỉnh** ở cuối luồng: service SHALL chạy giải
citation và kiểm grounding sau khi model sinh xong, rồi sự kiện chốt SHALL mang danh sách citation, hoặc — khi
câu trả lời khẳng định mà không có căn cứ hợp lệ — SHALL mang nội dung thay thế không‑đủ‑căn‑cứ. **Trạng thái
chốt của câu trả lời streaming SHALL trùng khớp với kết quả của endpoint blocking trên cùng đầu vào.**

Budget SHALL được ghi vào `chat_logs` với số lượt gọi đã dùng **kể cả khi client ngắt kết nối** giữa luồng
sau khi model đã được gọi. Câu được fast‑path bởi định tuyến ý định SHALL phát preset trong một sự kiện chốt,
không stream token giả.

#### Scenario: Stream câu trả lời có căn cứ
- **WHEN** client gọi `/chat/stream` với câu hỏi khớp dữ liệu
- **THEN** luồng phát status rồi các token câu trả lời, và sự kiện chốt mang citations giải từ marker `[n]`
- **AND** trạng thái cuối cùng giống hệt câu trả lời của endpoint blocking cho cùng câu hỏi

#### Scenario: Fail‑closed dưới streaming
- **WHEN** model stream một câu khẳng định không chứa marker hợp lệ và không phải dạng "không tìm thấy"
- **THEN** sự kiện chốt mang nội dung thay thế không‑đủ‑căn‑cứ để phía hiển thị hoán text tạm, không giữ lại text ungrounded

#### Scenario: Client ngắt giữa luồng
- **WHEN** client đóng kết nối sau khi model đã được gọi nhưng trước khi luồng kết thúc
- **THEN** service dừng sinh và vẫn ghi `chat_logs` với số lượt gọi đã dùng, budget không bị rò

#### Scenario: Câu mở rộng phạm vi qua streaming
- **WHEN** câu hỏi ở chế độ per‑insight kích hoạt mở rộng (sentinel)
- **THEN** luồng phát status báo đang tìm toàn hệ thống trước khi stream câu trả lời mở rộng, và sự kiện chốt mang `mode="expanded"` cùng citations từ index toàn cục

### Requirement: Xếp hạng lai vector + lexical qua RRF, không ngưỡng

Ở chế độ toàn cục (và ở phần mở rộng của chế độ per‑insight), tầng độ‑liên‑quan của xếp hạng SHALL trộn hai
tín hiệu: **tương đồng ngữ nghĩa** (cosine giữa embedding câu hỏi và embedding insight) và **so khớp từ khoá**
(độ liên quan lexical theo biên từ), bằng **Reciprocal Rank Fusion** dạng `1/(60 + rank)`. Điểm RRF SHALL là
khoá xếp hạng chính; `delivery_engine.score_for_role()` SHALL giữ vai trò khoá phụ; và service SHALL cắt
`chat_index_top_k` **sau** khi xếp hạng.

Service SHALL KHÔNG áp ngưỡng similarity cứng để loại tin: vector chỉ dùng để **xếp hạng tốt hơn**, không để
lọc, nên tập candidate SHALL KHÔNG bao giờ rỗng vì lý do độ tương đồng thấp.

#### Scenario: Câu hỏi ngữ nghĩa lệch từ khoá
- **WHEN** người dùng hỏi bằng từ ngữ khác với chữ trong tin (ví dụ "cắt giảm nhân sự" trong khi tin ghi *layoff*)
- **THEN** tin liên quan về ngữ nghĩa vẫn được xếp đủ cao để nằm trong index top‑K, không bị cắt vì không trùng từ khoá

#### Scenario: Không có ngưỡng loại tin
- **WHEN** không tin nào đạt độ tương đồng vector cao
- **THEN** service vẫn xếp hạng và trả về top‑K tin tốt nhất theo RRF, không trả về danh sách rỗng vì ngưỡng

#### Scenario: Khớp chính xác vẫn được giữ nhờ tầng lexical
- **WHEN** câu hỏi chứa một định danh chính xác (tên model, số phiên bản, mã lỗi)
- **THEN** tín hiệu lexical trong RRF vẫn đẩy tin chứa đúng chuỗi đó lên, không bị vector làm loãng

### Requirement: Duy trì embedding cho insight và suy giảm êm khi embedding vắng

Hệ thống SHALL sinh và lưu một vector embedding cho mỗi insight khi insight được publish, và SHALL cho phép
backfill embedding cho insight đã có. Việc sinh embedding SHALL dùng cùng nhà cung cấp Vertex với chiều cố
định, và SHALL KHÔNG dùng ngân sách quota của generation.

Khi embedding của câu hỏi không tạo được (lỗi/timeout) hoặc khi một insight chưa có embedding, service SHALL
suy giảm êm: xếp hạng bằng tầng lexical mà KHÔNG làm hỏng câu trả lời. Lỗi sinh embedding của một insight
SHALL KHÔNG chặn việc tạo insight đó.

#### Scenario: Embedding câu hỏi lỗi
- **WHEN** lời gọi sinh embedding cho câu hỏi thất bại
- **THEN** service xếp hạng bằng tầng lexical và vẫn trả lời được; không trả lỗi cho người dùng

#### Scenario: Insight chưa có embedding
- **WHEN** một insight `published` chưa được backfill embedding (embedding NULL)
- **THEN** insight đó vẫn tham gia xếp hạng qua tầng lexical và không bị loại khỏi tập candidate

#### Scenario: Lỗi embedding khi publish insight
- **WHEN** sinh embedding thất bại lúc publish một insight
- **THEN** insight vẫn được tạo với embedding NULL và hệ thống ghi cảnh báo, không làm hỏng pipeline analysis

### Requirement: Ghìm ngân sách suy luận của lượt sinh câu trả lời chat

Lượt gọi model sinh câu trả lời chat SHALL chạy với một **ngân sách token suy luận** giới hạn,
cấu hình được. Ngân sách này SHALL áp dụng **giống hệt nhau** cho cả lối trả lời một-phát lẫn
lối streaming — hai lối ra không được có cấu hình suy luận khác nhau.

Ngân sách SHALL KHÔNG áp lên các lượt gọi model của pipeline phân tích (gate, deep analysis) và
của bộ phân loại ý định: chúng là tác vụ nền, độ trễ không nằm trên đường phục vụ người dùng.

Việc điều chỉnh ngân sách SHALL do cổng chất lượng quyết định: khi Faithfulness tụt dưới ngưỡng
hoặc Citation Precision không còn tuyệt đối, hệ thống SHALL nâng ngân sách chứ KHÔNG hạ ngưỡng.

#### Scenario: Câu tra cứu thường
- **WHEN** người dùng hỏi một câu tra cứu ở chế độ toàn cục
- **THEN** lượt gọi model chạy với ngân sách suy luận đã cấu hình, và câu trả lời vẫn kèm
  citation hợp lệ như trước

#### Scenario: Hai lối ra dùng chung cấu hình
- **WHEN** cùng một câu hỏi đi qua lối một-phát và lối streaming
- **THEN** cả hai lượt gọi model mang cùng ngân sách suy luận

#### Scenario: Pipeline phân tích không bị ảnh hưởng
- **WHEN** gate hoặc deep analysis chạy trên một tài liệu
- **THEN** lượt gọi model của chúng giữ nguyên hành vi suy luận như trước thay đổi này

### Requirement: Đo được số token suy luận đã dùng

Hệ thống SHALL ghi lại số token suy luận mà mỗi lượt trả lời chat tiêu thụ, ở dạng đọc được
trực tiếp chứ không phải suy ra từ hiệu của các số đếm khác.

#### Scenario: Một lượt trả lời chat kết thúc
- **WHEN** một lượt trả lời chat hoàn tất
- **THEN** số token suy luận của lượt đó được ghi lại cùng các số đếm chi phí khác

#### Scenario: Nhà cung cấp không báo cáo số token suy luận
- **WHEN** phản hồi của model không mang số token suy luận
- **THEN** hệ thống ghi giá trị rỗng và vẫn hoàn tất lượt trả lời bình thường

### Requirement: Chuẩn bị ngữ cảnh chạy song song

Hệ thống SHALL chạy song song hai bước chuẩn bị ngữ cảnh độc lập nhau — sinh embedding cho câu
hỏi và nạp tập ứng viên từ kho dữ liệu — thay vì nối tiếp.

Hệ thống SHALL KHÔNG sinh embedding cho câu hỏi mà tầng xếp hạng đã xác định là không dùng tới
kết quả đó: lượt gọi ấy phải được **bỏ hẳn**, không phải thực hiện rồi vứt kết quả.

#### Scenario: Câu hỏi có từ khoá nội dung
- **WHEN** người dùng hỏi một câu mang từ khoá nội dung ở chế độ toàn cục
- **THEN** embedding câu hỏi và việc nạp ứng viên diễn ra đồng thời, tổng thời gian chuẩn bị
  xấp xỉ bước chậm hơn trong hai bước

#### Scenario: Câu hỏi rỗng từ khoá
- **WHEN** người dùng hỏi một câu mà mọi từ đều là stopword
- **THEN** hệ thống không gọi sinh embedding cho câu đó

