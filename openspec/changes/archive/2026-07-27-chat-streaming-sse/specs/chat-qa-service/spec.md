## ADDED Requirements

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
