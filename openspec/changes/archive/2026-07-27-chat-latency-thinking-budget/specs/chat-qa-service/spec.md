## ADDED Requirements

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
