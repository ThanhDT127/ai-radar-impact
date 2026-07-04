## MODIFIED Requirements

### Requirement: Tái cấu trúc giao diện thẻ InsightCard

Thẻ thông tin `InsightCard` MUST được thiết kế lại theo hướng tinh gọn và dễ quét (scannable), chuyển từ cấu trúc nặng văn bản (text-heavy) sang cấu trúc phân tầng thông tin rõ ràng.

#### Scenario: Cấu trúc các dòng thông tin trên thẻ
- **WHEN** thẻ `InsightCard` được hiển thị trên dashboard
- **THEN** Row 1 ở đầu card MUST hiển thị nhãn phân tầng (`intelligence_tier`) và thời gian đăng bài (`relative_time`)
- **THEN** Row 2 MUST hiển thị các nhãn chủ đề (`topic tags`) và loại sự kiện (`event_type`)
- **THEN** Title block MUST hiển thị tên nguồn bài viết (`source_name`), tiêu đề tiếng Việt (dạng bold) và tiêu đề phụ tiếng Anh (nếu có và khác tiêu đề tiếng Việt)

#### Scenario: Danh sách tóm tắt dạng bullet points
- **WHEN** thẻ render phần nội dung tóm tắt chính (body)
- **THEN** thẻ MUST hiển thị tối đa 5 gạch đầu dòng (`bullets`) thay thế cho 2 khối văn bản "Điểm chính" và "Đáng chú ý" trước đây
- **AND** các gạch đầu dòng này SHALL được lấy từ các trường dữ liệu `signal`, `so_what`, `why_it_matters` và phân tách từ `summary_short`

#### Scenario: Loại bỏ danh sách vai trò bị ảnh hưởng trên card
- **WHEN** thẻ render thông tin tags
- **THEN** thẻ MUST không hiển thị danh sách các vai trò bị ảnh hưởng ("Ai bị ảnh hưởng") để giảm thiểu rối mắt
- **AND** thông tin các vai trò bị ảnh hưởng SHALL chỉ được hiển thị ở trang chi tiết của Insight

#### Scenario: Footer chứa các chỉ số gọn gàng (Compact Footer)
- **WHEN** thẻ hiển thị phần chân trang (footer)
- **THEN** các chỉ số đo lường (actionability score, trust score, adoption ring, momentum) MUST được sắp xếp nằm ngang trên một dòng đơn giản
- **AND** các chỉ số này SHALL được ngăn cách bởi dấu chấm trung tâm (`·`) rõ ràng
