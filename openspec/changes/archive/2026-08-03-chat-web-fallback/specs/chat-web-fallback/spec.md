## ADDED Requirements

### Requirement: Tra cứu ngoài được kích hoạt bởi tín hiệu từ chính lượt trả lời

Khi ngữ cảnh từ corpus không đủ để trả lời một phần của câu hỏi, model SHALL phát sentinel
mang tham số `[[TRA_CỨU_NGOÀI: <truy vấn>]]` **kèm theo** phần trả lời được từ corpus.

Truy vấn tìm kiếm SHALL do model viết, KHÔNG do server ghép từ khoá và KHÔNG do một bộ phân
loại riêng quyết định.

Sentinel SHALL được phát **dè dặt**: chỉ khi câu hỏi hỏi tới một thực thể hoàn toàn vắng khỏi
dữ liệu. Khi phân vân, model SHALL KHÔNG phát sentinel.

Service SHALL dò sentinel **trước** khi áp `enforce_grounding`.

#### Scenario: Câu hỏi ghép, một vế có trong corpus
- **WHEN** câu hỏi yêu cầu so sánh một thực thể có trong corpus với một thực thể không có
- **THEN** model trả lời vế có dữ liệu và phát sentinel kèm truy vấn cho vế còn thiếu

#### Scenario: Corpus trả lời được toàn bộ
- **WHEN** dữ liệu đủ để trả lời cả câu hỏi
- **THEN** sentinel SHALL KHÔNG được phát và không có lượt tra cứu nào

#### Scenario: Sentinel không bị grounding nuốt
- **WHEN** câu trả lời chứa sentinel
- **THEN** tín hiệu được nhận trước khi `enforce_grounding` có thể thay thế câu trả lời

### Requirement: Tra cứu lấy định danh nguồn, nội dung lấy từ chính trang nguồn

Bước tra cứu SHALL dùng Grounding with Google Search và SHALL chỉ lấy **định danh nguồn**
(`uri`, `title`) từ kết quả.

Nội dung văn bản của mỗi nguồn SHALL được lấy bằng cách **tải chính trang đó** và trích xuất
nội dung chính, KHÔNG dùng bản diễn giải do model viết lại.

Lý do: nếu văn bản là bản diễn giải của model mà citation lại trỏ tới trang gốc, thì diễn giải
sai sẽ tạo ra một khẳng định có nguồn hợp lệ nhưng trang nguồn không hề nói — đúng chế độ hỏng
mà mô hình trích dẫn của hệ thống sinh ra để chặn.

Văn bản lấy về SHALL bị cắt theo cùng trần độ dài đang áp cho nội dung bài gốc trong ngữ cảnh.

#### Scenario: Tải trang thành công
- **WHEN** ít nhất một uri tải được và trích xuất được nội dung
- **THEN** nguồn đó vào ngữ cảnh với văn bản nguyên văn của trang, kèm uri của chính nó

#### Scenario: Một phần uri tải hỏng
- **WHEN** một số uri trả về lỗi, paywall, hoặc không trích xuất được nội dung
- **THEN** các nguồn còn lại vẫn được dùng và lượt trả lời vẫn hoàn tất

#### Scenario: Tất cả uri tải hỏng
- **WHEN** không uri nào lấy được nội dung
- **THEN** service SHALL rơi về phần văn bản do bước tra cứu sinh ra, gắn nhãn rõ là tóm tắt
  chưa đối chiếu nguyên văn, và SHALL KHÔNG trả lỗi HTTP

#### Scenario: Không tìm được nguồn nào
- **WHEN** bước tra cứu không trả về uri nào
- **THEN** service trả lời phần có trong corpus và nói rõ phần không tra cứu được

### Requirement: Nguồn web dùng chung một dãy số và một bảng ánh xạ với insight

Nguồn web SHALL được server cấp phát số `[n]` **nối tiếp** trong cùng dãy số với insight, và
SHALL nằm trong **cùng một** bảng ánh xạ.

Prompt SHALL KHÔNG chứa uri, định danh insight, hay bất kỳ định danh nào — model chỉ thấy số.

Citation SHALL mang trường phân biệt kiểu nguồn, và SHALL giữ nguyên trường `n` tường minh.
Client SHALL giải marker bằng cách tra theo `n`, KHÔNG bằng vị trí trong mảng.

Server SHALL KHÔNG đánh số lại marker trong câu trả lời.

#### Scenario: Lượt có cả nguồn hệ thống và nguồn web
- **WHEN** ngữ cảnh gồm cả insight và nguồn web
- **THEN** dãy `[n]` liên tục và không số nào trỏ tới hai nguồn khác nhau

#### Scenario: Không có hai không gian số
- **WHEN** nguồn web được thêm vào ngữ cảnh
- **THEN** SHALL KHÔNG tồn tại một dãy số thứ hai dành riêng cho nguồn web

### Requirement: Nội dung tra cứu là dữ liệu, không phải chỉ thị

Prompt SHALL nêu tường minh rằng khối nội dung tra cứu là **dữ liệu tham khảo**, và mọi câu
mang tính ra lệnh xuất hiện bên trong nó SHALL bị bỏ qua.

#### Scenario: Trang chứa chỉ thị chèn vào
- **WHEN** một trang được tải về chứa câu ra lệnh nhằm thay đổi hành vi của trợ lý
- **THEN** trợ lý SHALL KHÔNG tuân theo và SHALL tiếp tục trả lời theo luật của hệ thống

### Requirement: Tra cứu có ngân sách riêng và không chặn câu trả lời

Số lượt tra cứu mỗi ngày SHALL được đếm bằng một bộ đếm **riêng**, tách khỏi bộ đếm lượt gọi
model của chat — hai loại có đơn giá khác nhau.

Khi ngân sách tra cứu cạn, service SHALL vẫn trả lời phần có trong corpus và nói rõ không tra
cứu được, SHALL KHÔNG trả lỗi hết quota.

Tính năng SHALL mặc định **tắt**. Khi tắt, prompt SHALL KHÔNG mang luật sentinel tra cứu và
hành vi SHALL trùng khít bản chưa có tính năng này.

#### Scenario: Ngân sách tra cứu cạn
- **WHEN** số lượt tra cứu trong ngày đã đạt trần
- **THEN** câu hỏi vẫn được trả lời từ corpus, không có lỗi quota

#### Scenario: Tính năng tắt
- **WHEN** cờ bật/tắt ở trạng thái tắt
- **THEN** không lượt tra cứu nào xảy ra và câu trả lời giống hệt trước change này

### Requirement: Hiển thị Search Suggestions khi có tra cứu

Khi một lượt trả lời có dùng Grounding with Google Search, giao diện SHALL hiển thị khối
Search Suggestions do nhà cung cấp trả về. Đây là yêu cầu tuân thủ điều khoản sử dụng, không
phải hạng mục trang trí.

#### Scenario: Lượt có tra cứu
- **WHEN** câu trả lời được dựng có dùng tra cứu ngoài
- **THEN** khối Search Suggestions được hiển thị kèm câu trả lời

#### Scenario: Lượt không tra cứu
- **WHEN** câu trả lời chỉ dùng dữ liệu trong hệ thống
- **THEN** khối Search Suggestions SHALL KHÔNG hiển thị
