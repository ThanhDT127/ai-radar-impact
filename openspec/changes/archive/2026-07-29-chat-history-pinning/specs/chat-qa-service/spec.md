## ADDED Requirements

### Requirement: Tin đã trích trong lịch sử được ghim vào ngữ cảnh lượt hiện tại

Service SHALL bảo đảm **N tin được trích gần nhất** trong `history` có mặt trong index của lượt
hiện tại, bất kể thứ hạng của chúng theo `_rank`. N là `chat_history_pin_slots` (mặc định 3);
`0` SHALL tắt hoàn toàn cơ chế này và cho hành vi trùng khít bản chưa có nó.

Việc chọn tin ghim SHALL tất định theo **thứ tự nhắc gần nhất** (lượt mới trước lượt cũ), KHÔNG
chấm điểm liên quan và KHÔNG suy đoán ý định câu hỏi.

Đây là phiên bản **thu hẹp** của bất biến do `chat-context-depth` tuyên bố (*mọi* tin được nhắc
trong history đều còn mặt trong ngữ cảnh). Bản nguyên văn không thực thi được: history đầy có
thể nhắc tới ~25 tin, mà ghim quá 6 chỗ làm recall@K tụt khỏi baseline.

#### Scenario: Tin đã bàn rơi khỏi top-K khi người dùng đổi chủ đề
- **WHEN** một tin được trích ở lượt trước, và ở lượt hiện tại nó xếp hạng ngoài `chat_index_top_k`
- **THEN** tin đó vẫn có mặt trong index của lượt hiện tại kèm dòng dữ liệu nén của nó

#### Scenario: Số tin trong history vượt số chỗ ghim
- **WHEN** history nhắc tới nhiều tin hơn `chat_history_pin_slots`
- **THEN** chỉ N tin được trích **gần nhất** được ghim, các tin cũ hơn cạnh tranh bình thường theo thứ hạng

#### Scenario: Tắt cơ chế
- **WHEN** `chat_history_pin_slots = 0`
- **THEN** index chỉ gồm tin do `_rank` chọn, giống hệt hành vi trước change này

#### Scenario: Lượt lịch sử không kèm định danh nguồn
- **WHEN** client cũ gửi `history` mà các lượt không mang định danh insight
- **THEN** service SHALL không ghim gì và SHALL không báo lỗi

### Requirement: Tin ghim không trùng số và không chiếm chỗ ô sâu

Trước khi ghim, service SHALL khử trùng theo định danh insight: tin đã có mặt trong index hoặc
trong ô sâu SHALL KHÔNG được cấp một số `[n]` thứ hai.

Tin ghim SHALL vào **index nén**, KHÔNG vào ô sâu. Ô sâu dành cho working set do người dùng chủ
động chọn; tin trong lịch sử cần **có mặt** chứ không cần **đọc kỹ**.

#### Scenario: Tin đã bàn vẫn còn trong top-K
- **WHEN** một tin được trích ở lượt trước và vẫn xếp hạng trong `chat_index_top_k`
- **THEN** nó xuất hiện đúng **một** lần trong index, mang đúng **một** số `[n]`

#### Scenario: Tin đã bàn đang nằm trong working set
- **WHEN** một tin vừa được trích ở lượt trước vừa nằm trong `referenced_insight_ids`
- **THEN** nó được phục vụ ở ô sâu và SHALL KHÔNG bị ghim thêm một lần nữa vào index

### Requirement: Tin ghim xếp cuối index

Tin được ghim vì lịch sử SHALL đặt ở **cuối** danh sách index, sau các tin do `_rank` chọn.

Lý do: prompt hệ thống dặn model rằng tin ở đầu danh sách đáng chọn hơn. Tin ghim theo định
nghĩa không liên quan tới câu hỏi của lượt hiện tại — nó có mặt để làm chỗ dựa cho tham chiếu
trong lịch sử, không phải để làm câu trả lời.

#### Scenario: Thứ tự trong index
- **WHEN** index gồm cả tin xếp hạng lẫn tin ghim
- **THEN** mọi tin xếp hạng đứng trước mọi tin ghim, và dãy số `[n]` vẫn liên tục không đứt

#### Scenario: Chế độ mở rộng đánh số từ 2
- **WHEN** lượt trả lời ở chế độ mở rộng, nơi `[1]` dành cho bài đang xem
- **THEN** tin ghim nhận các số cuối của cùng một dãy liên tục, không mở một không gian số thứ hai

### Requirement: Định danh insight trong lượt lịch sử được kiểm chứng phía server

Khi client gửi định danh insight kèm mỗi lượt lịch sử, service SHALL nạp chúng qua **đúng một
đường nạp** dùng chung với working set — lọc `status = published` — và SHALL bỏ **lặng lẽ**
định danh không phân giải được.

"Đúng một đường nạp" là ràng buộc mạnh hơn "bộ lọc chặt nhất": hai đường với hai bộ lọc hơi
khác nhau là cách chắc chắn để một hôm nào đó ghim được thứ mà working set không nạp nổi, hoặc
ngược lại, mà không có gì báo lỗi.

Ranh giới tin cậy không đổi so với `referenced_insight_ids`: client có thể khiến một insight
**có thật** đi vào ngữ cảnh, nhưng KHÔNG thể đưa văn bản tuỳ ý vào prompt.

#### Scenario: Định danh không tồn tại
- **WHEN** một lượt lịch sử mang định danh insight không có trong repository
- **THEN** service bỏ qua định danh đó, vẫn trả lời bình thường, không trả lỗi

#### Scenario: Định danh trỏ insight chưa publish
- **WHEN** định danh trỏ một insight chưa `published`
- **THEN** insight đó SHALL KHÔNG được ghim vào ngữ cảnh

## MODIFIED Requirements

### Requirement: Trần top-K cho index
Service SHALL cắt index ở `chat_index_top_k` tin **sau khi xếp hạng** (0 = không giới hạn). Khi có tin bị cắt, prompt SHALL cho model biết tổng số tin thực tế khớp để con số "còn N tin khác" không bị thiếu. Việc xác định "vai trò không có tin nào" SHALL tính trên **toàn bộ tập khớp trước khi cắt**.

`chat_index_top_k` là **TỔNG** số tin vào prompt: ô sâu VÀ tin ghim vì lịch sử đều tính trong
trần này. Ghim N chỗ vì thế đẩy N tin ở **đuôi** bảng xếp hạng ra khỏi index, và ngân sách token
không phình lên.

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

#### Scenario: Ghim vì lịch sử chiếm chỗ trong trần
- **WHEN** `chat_history_pin_slots = 3` và có 3 tin cần ghim chưa nằm trong top-K
- **THEN** index vẫn chứa đúng `chat_index_top_k` tin, trong đó 3 tin xếp hạng thấp nhất bị đẩy ra

### Requirement: Marker trong lịch sử hội thoại giải thành tiêu đề

Khi dựng khối lịch sử hội thoại đưa vào prompt, service SHALL thay mọi marker nguồn dạng `[n]` trong các
lượt trước bằng nhãn nhận diện được của insight tương ứng (tiêu đề), thay vì giữ nguyên con số.

Lý do: bảng ánh xạ `n → insight` được dựng lại theo từng lượt, nên một con số trong lịch sử có thể trỏ
insight khác ở lượt hiện tại.

Nhãn nguồn của mỗi lượt SHALL mang thêm **định danh insight** để service ghim được tin đó vào
ngữ cảnh lượt hiện tại. Chỉ nhãn hiển thị thôi thì không đủ: khớp ngược theo tiêu đề là phép mờ
và một lần tra nhầm sẽ ghim sai tin trong im lặng.

#### Scenario: Số marker bị tái sử dụng qua các lượt
- **WHEN** một lượt trước trích `[3]` cho insight X và lượt hiện tại đánh số `[3]` cho insight Y
- **THEN** khối lịch sử đưa vào prompt nhắc tới X bằng tiêu đề, và model không hiểu nhầm `[3]` của lượt trước là Y

#### Scenario: Lượt lịch sử mang định danh nguồn
- **WHEN** client gửi một lượt trợ lý kèm danh sách nguồn của chính lượt đó
- **THEN** mỗi nguồn mang cả số marker, tiêu đề hiển thị, và định danh insight dùng để ghim
