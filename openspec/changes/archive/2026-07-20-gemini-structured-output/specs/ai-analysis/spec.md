## ADDED Requirements

### Requirement: Đầu ra gate ràng buộc bằng schema
Lần gọi Gemini cho **gate pre-screening** MUST khai báo `response_schema` cho API, không chỉ
`response_mime_type`. Tập đóng `content_type` MUST được biểu diễn thành enum trong schema, và schema
MUST dựng từ chính hằng số trong `app/ai/prompts.py` — KHÔNG chép tay giá trị, để schema không trôi
khỏi tập đóng.

Lần gọi **deep analysis** MUST KHÔNG dùng `response_schema`. Đã thử và đo (20/07/2026): ràng buộc
schema khiến model sinh trường văn bản tự do (`why_it_matters`) lặp vô nghĩa tới ~6500 ký tự cho tới
khi chạm `max_output_tokens` và bị cắt giữa chuỗi, làm 100% document qua gate lỗi parse. `max_length`
trong schema KHÔNG cứu được vì Vertex không thực thi ràng buộc đó. Tập đóng ở nhánh này do lớp
validate post-parse bảo đảm.

#### Scenario: Gate không trả được `content_type` ngoài tập đóng
- **WHEN** Gemini gate định gán `content_type = "tutorial"` (không thuộc `ALLOWED_CONTENT_TYPES`)
- **THEN** API từ chối giá trị đó do ràng buộc enum

#### Scenario: Thêm giá trị vào tập đóng
- **WHEN** một giá trị mới được thêm vào `ALLOWED_CONTENT_TYPES` trong `prompts.py`
- **THEN** schema gửi cho Gemini tự động chứa giá trị đó, không cần sửa thêm chỗ nào khác

#### Scenario: Deep analysis giữ đầu ra không ràng buộc schema
- **WHEN** `analyze` gọi Gemini
- **THEN** config KHÔNG chứa `response_schema`; tập đóng được bảo đảm bởi `_validate_recommendations` / `_validate_affected_roles` / `_validate_adoption_ring`

### Requirement: Fail-open phải để lại dấu vết
Khi gate lỗi và document được cho đi thẳng vào deep analysis (fail-open), hệ thống MUST ghi lại rằng
document đó **chưa được gate chấm**. Thống kê tỉ lệ qua gate MUST loại các document này ra, vì chúng
không phải bằng chứng nội dung đạt chuẩn.

#### Scenario: Gate lỗi parse
- **WHEN** `gate_analyze` trả về lỗi parse JSON cho một document
- **THEN** document vẫn được deep analysis (giữ nguyên fail-open) **và** được đánh dấu là đã bỏ qua gate

#### Scenario: Thống kê không tính document bỏ qua gate
- **WHEN** tính tỉ lệ qua gate của một nguồn
- **THEN** các document có dấu bỏ qua gate không được tính vào tử số lẫn mẫu số

### Requirement: Log đủ dài để chẩn đoán lỗi parse
Khi parse JSON thất bại, hệ thống MUST log phần raw response đủ dài để nhìn thấy vị trí gây lỗi. Log
dài chỉ áp dụng ở nhánh lỗi, không áp cho đường chạy bình thường.

#### Scenario: Lỗi ở vị trí xa đầu chuỗi
- **WHEN** JSON hỏng ở ký tự thứ 517 của response
- **THEN** log chứa đủ nội dung để thấy ký tự đó, không bị cắt trước vị trí lỗi
