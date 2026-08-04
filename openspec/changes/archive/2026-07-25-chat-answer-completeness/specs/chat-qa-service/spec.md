## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Chat không dùng structured output
Lời gọi Gemini cho chat SHALL KHÔNG đặt `response_mime_type="application/json"` và SHALL KHÔNG khai báo `response_schema`; câu trả lời SHALL là text thuần.

#### Scenario: Câu trả lời dài
- **WHEN** model sinh câu trả lời dài chạm `max_output_tokens`
- **THEN** không có lỗi parse JSON làm hỏng toàn bộ request; phần đã sinh SHALL được xử lý theo yêu cầu "Câu trả lời chat không bao giờ dở dang" (hỏi lại, rồi cắt về ranh giới câu) thay vì trả thẳng cho client
