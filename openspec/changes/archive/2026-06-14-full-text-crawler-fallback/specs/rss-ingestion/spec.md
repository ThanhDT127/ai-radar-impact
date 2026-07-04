## ADDED Requirements

### Requirement: Trigger fallback extraction dynamically
Module M2 khi cào tin RSS phải nhận diện được khi nào nội dung RSS không đủ dùng để gọi cơ chế cào full-text thay thế.

#### Scenario: Short RSS snippet detected
- **WHEN** độ dài thuộc tính `content` hoặc `summary` thu được từ RSS có dưới 500 ký tự.
- **THEN** gọi hàm `_fetch_full_text_with_cloak` truyền vào URL gốc của bài viết.
- **AND WHEN** hàm này trả về kết quả thành công và dài hơn đoạn RSS hiện tại.
- **THEN** ghi đè nội dung gốc bằng kết quả thu được từ Trafilatura để lưu vào cột `raw_content`.
