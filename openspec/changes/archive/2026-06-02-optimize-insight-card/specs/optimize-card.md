## MODIFIED Requirements

### Requirement: Tối ưu hiển thị các gạch đầu dòng (bullets) trên InsightCard

Để tránh trùng lặp thông tin hiển thị trên giao diện thẻ, hàm `generateCardBullets` trong `InsightCard.tsx` MUST nhận thêm tham số `displayTitle` và SHALL tự động loại bỏ nội dung từ `summary_short` ra khỏi danh sách `bullets` nếu `summary_short` được dùng làm tiêu đề hiển thị (`displayTitle`).

#### Scenario: Tiêu đề hiển thị trùng với summary_short (Tiêu đề gốc là tiếng Anh)
- **WHEN** một `Insight` có tiêu đề gốc bằng tiếng Anh và trường `summary_short` được chọn làm tiêu đề hiển thị `displayTitle`
- **THEN** danh sách `bullets` hiển thị trên `InsightCard` MUST không chứa các câu được tách từ `summary_short` để tránh trùng lặp
- **AND** danh sách `bullets` vẫn hiển thị tối đa 5 phần tử chất lượng được lấy từ các trường `signal`, `so_what` và `why_it_matters`

#### Scenario: Tiêu đề hiển thị không trùng với summary_short (Tiêu đề gốc chứa tiếng Việt)
- **WHEN** một `Insight` có tiêu đề gốc chứa tiếng Việt và `displayTitle` không trùng với `summary_short`
- **THEN** danh sách `bullets` hiển thị trên `InsightCard` SHALL vẫn chứa các câu được phân tách từ `summary_short` (nếu có)
- **AND** số lượng phần tử của `bullets` vẫn được giới hạn tối đa là 5 phần tử
