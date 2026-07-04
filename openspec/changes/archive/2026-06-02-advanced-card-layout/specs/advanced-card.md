## MODIFIED Requirements

### Requirement: Tách cấu trúc thẻ InsightCard thành Vùng Tín hiệu Kỹ thuật và Vùng Phân tích Nhanh

Giao diện thẻ `InsightCard` MUST hỗ trợ hiển thị nổi bật các thuộc tính kỹ thuật thực hành (Technical Signals) ở một vùng riêng biệt và giới hạn số lượng bullet points ở phần nội dung tóm tắt để giữ thẻ tinh gọn.

#### Scenario: Hiển thị các chỉ số Technical Signals dạng Badges
- **WHEN** một `Insight` có ít nhất một trong các thuộc tính boolean (`has_code_example`, `has_benchmark`, `has_api_change`, `has_security_patch`) là `true`
- **THEN** thẻ `InsightCard` MUST hiển thị một hàng "Tín hiệu Kỹ thuật" nằm ngay dưới tiêu đề
- **AND** các badges tương ứng với giá trị `true` SHALL được render rõ ràng:
  * `has_code_example` ➔ `💻 Có code mẫu`
  * `has_benchmark` ➔ `📊 Có benchmark`
  * `has_api_change` ➔ `🔗 Thay đổi API`
  * `has_security_patch` ➔ `🛡️ Bảo mật`

#### Scenario: Không có tín hiệu kỹ thuật nào
- **WHEN** một `Insight` có cả bốn thuộc tính boolean trên đều là `false`
- **THEN** hàng "Tín hiệu Kỹ thuật" trên thẻ MUST tự động ẩn đi và không render bất kỳ khoảng trống thừa nào

#### Scenario: Giới hạn tối đa 3 bullet points
- **WHEN** thẻ `InsightCard` hiển thị danh sách các gạch đầu dòng tóm tắt (`bullets`)
- **THEN** số lượng bullets hiển thị trên thẻ MUST chỉ có tối đa 3 dòng (thay vì 5 dòng như trước) để đảm bảo thẻ gọn gàng
