## MODIFIED Requirements

### Requirement: Nâng cấp giao diện hiển thị các thẻ KPI thống kê

Các thẻ KPI thống kê trên đầu trang Dashboard (`KPISummary`) MUST được bổ sung thông tin ngữ cảnh, biểu tượng giải thích và phối màu trực quan để người dùng hiểu rõ ý nghĩa các chỉ số.

#### Scenario: Bố cục đầy đủ thông tin của thẻ KPI
- **WHEN** các thẻ KPI được hiển thị trên dashboard
- **THEN** mỗi thẻ KPI MUST hiển thị 4 thành phần chính: tiêu đề nhãn (label), biểu tượng tooltip ⓘ, số lượng tổng lớn, và chú thích phụ (subtitle) luôn hiển thị bên dưới
- **AND** tiêu đề nhãn SHALL được cập nhật rõ nghĩa hơn: "Tổng bản tin", "Ảnh hưởng cao", "Cơ hội hành động", "Nguồn hoạt động"

#### Scenario: Hiển thị tooltip giải thích chi tiết khi hover
- **WHEN** người dùng di chuột (hover) vào biểu tượng ⓘ bên cạnh nhãn của bất kỳ thẻ KPI nào
- **THEN** hệ thống MUST hiển thị một khung thông tin giải thích (tooltip) chi tiết về nguồn gốc và cách tính của chỉ số đó
- **AND** tooltip này SHALL sử dụng component `<Tooltip>` từ hệ thống tooltip chung

#### Scenario: Phối màu cảnh báo trực quan theo ngữ cảnh (Semantic Colors)
- **WHEN** thẻ KPI "Ảnh hưởng cao" (urgency critical/high) được hiển thị
- **THEN** con số thống kê hoặc nền phụ của thẻ MUST sử dụng màu đỏ hoặc cam nổi bật để cảnh báo
- **WHEN** thẻ KPI "Cơ hội hành động" được hiển thị
- **THEN** con số thống kê hoặc nền phụ của thẻ MUST sử dụng màu xanh lá cây để biểu thị tín hiệu cơ hội phát triển
