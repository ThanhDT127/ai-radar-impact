## ADDED Requirements

### Requirement: Trả lời phần có căn cứ thay vì từ chối toàn bộ

Khi câu hỏi gồm nhiều vế và ngữ cảnh chỉ đủ căn cứ cho một phần, service SHALL trả lời phần có
căn cứ và SHALL nêu rõ phần còn thiếu, thay vì từ chối toàn bộ câu hỏi.

Trước change này, một câu hỏi so sánh mà thiếu một vế sẽ mất luôn cả vế đã có đủ dữ liệu trong
hệ thống.

Yêu cầu này SHALL độc lập với việc tra cứu ngoài có bật hay không: khi tra cứu tắt, service vẫn
phải trả lời phần có căn cứ.

#### Scenario: Câu hỏi so sánh, thiếu một vế
- **WHEN** người dùng hỏi so sánh giữa một chủ thể có dữ liệu và một chủ thể không có
- **THEN** câu trả lời trình bày dữ liệu của chủ thể có, kèm marker nguồn, và nói rõ vế còn lại
  không có trong hệ thống

#### Scenario: Không vế nào có căn cứ
- **WHEN** không phần nào của câu hỏi có căn cứ trong ngữ cảnh
- **THEN** service SHALL từ chối như hiện nay, không bịa

## MODIFIED Requirements

### Requirement: Auto‑fallback từ scope bài sang scope mở rộng

Ở chế độ per‑insight, khi câu hỏi rõ ràng **không thể trả lời từ nội dung bài đang xem**, service SHALL tự
mở rộng phạm vi sang toàn hệ thống thay vì trả lời cụt. Cơ chế: lượt gọi model ở chế độ per‑insight SHALL
được hướng dẫn phát một **sentinel văn bản thuần đã định nghĩa** khi (và chỉ khi) câu hỏi nằm ngoài phạm vi
bài; service phát hiện sentinel SHALL dựng **context mở rộng** gồm insight của bài đang xem **cộng** index
toàn cục đã xếp hạng, rồi gọi model **lần thứ hai** để trả lời.

Câu trả lời mở rộng SHALL nêu rõ rằng đã tìm trên toàn hệ thống, citation SHALL lấy từ bảng ánh xạ `[n]` của
index toàn cục, và `mode` SHALL là `"expanded"`. Service SHALL KHÔNG dùng `response_schema` để phát/đọc
sentinel. Sentinel SHALL được phát **dè dặt**: câu hỏi còn trả lời được dù chỉ một phần từ nội dung bài
SHALL KHÔNG kích hoạt mở rộng.

Service SHALL KHÔNG dùng một lượt gọi model riêng chỉ để phân loại phạm vi; tín hiệu ngoài‑phạm‑vi SHALL là
kết quả của chính lượt gọi trả lời per‑insight.

Tổng số **bước trả lời** cho một câu hỏi SHALL KHÔNG vượt quá **3** (trước đây là 2; bước thứ ba dành cho
đường tra cứu ngoài). Một bước MAY tiêu nhiều hơn một lượt gọi tính tiền khi câu trả lời bị cắt và phải hỏi
lại; trần áp lên số bước, còn bộ đếm budget SHALL ghi số lượt thực đã tốn tiền. Bước **tải nội dung trang
web** SHALL KHÔNG tính là một bước trả lời.

Đường mở rộng phạm vi và đường tra cứu ngoài SHALL loại trừ nhau trong cùng một lượt: chế độ per‑insight
SHALL KHÔNG phát sentinel tra cứu ngoài.

Chạm trần SHALL KHÔNG bao giờ thoát ra thành lỗi HTTP 500.

#### Scenario: Câu hỏi cần mở rộng rồi cần tra cứu
- **WHEN** câu hỏi ở chế độ per-insight không trả lời được và sau khi mở rộng vẫn thiếu dữ kiện
- **THEN** lượt mở rộng là nơi phát sentinel tra cứu, và tổng số bước không vượt 3

#### Scenario: Chế độ per-insight
- **WHEN** người dùng hỏi trong phạm vi một bài
- **THEN** chỉ sentinel ngoài-phạm-vi được phép phát, sentinel tra cứu ngoài SHALL KHÔNG phát

#### Scenario: Chạm trần
- **WHEN** một lượt chạm trần số bước
- **THEN** người dùng nhận được câu trả lời hoặc câu từ chối hợp lệ, không phải lỗi máy chủ
