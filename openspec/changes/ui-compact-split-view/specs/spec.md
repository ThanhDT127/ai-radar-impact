## ADDED Requirements

### Requirement: Split View Layout on Detail Page
Trang chi tiết của insight phải hỗ trợ hiển thị song song bản phân tích tiếng Việt của Gemini và bài viết gốc tiếng Anh theo dạng Split View 50/50, giúp người dùng đối chiếu thông tin dễ dàng.

#### Scenario: Display Split View when original content exists
- **WHEN** Người dùng truy cập trang chi tiết của một insight có chứa nội dung bài viết gốc (`content_text` không rỗng)
- **THEN** Giao diện sẽ hiển thị 2 cột bằng nhau (50/50): cột bên trái chứa bản dịch và phân tích AI tiếng Việt, cột bên phải chứa bài viết gốc tiếng Anh. Cả hai cột đều có thể cuộn (scroll) độc lập.

#### Scenario: Fallback to single column when original content is missing
- **WHEN** Người dùng truy cập trang chi tiết của một insight không có nội dung bài viết gốc (`content_text` là null hoặc rỗng)
- **THEN** Cột bài viết gốc bên phải sẽ bị ẩn hoàn toàn, và cột phân tích tiếng Việt bên trái sẽ tự động giãn rộng ra chiếm 100% không gian hiển thị.

---

### Requirement: Compact Metadata Ribbon on Detail Page
Loại bỏ sidebar 30% cồng kềnh chứa 6 cards thông tin riêng lẻ, thay bằng một dải Ribbon Metadata nằm ngang, tối giản, hiển thị ngay bên dưới tiêu đề trang chi tiết.

#### Scenario: Display consolidated metadata in ribbon
- **WHEN** Người dùng xem trang chi tiết insight
- **THEN** Hệ thống hiển thị 1 dải ribbon nằm ngang có chiều cao khoảng 80px, gom gọn các nhóm thông tin bao gồm: điểm tin cậy (Trust Score), điểm khả thi (Actionability Score), các đối tượng bị ảnh hưởng (Roles), phân loại (Tier, Event Type), các chỉ số thực tế (Practical Indicators), và nguồn bài viết (Source) kèm thời gian xuất bản.

---

### Requirement: Uniform Cards with Inline Thumbnail on List Page
Mọi card hiển thị trên danh sách insight (`InsightList`) phải có kích thước và bố cục đồng đều nhau, không sử dụng layout card nổi bật (featured card) chiếm 2 cột. Ảnh đại diện của card phải thu nhỏ thành thumbnail inline nằm bên phải phần nội dung chữ.

#### Scenario: Render uniform grid without featured card
- **WHEN** Người dùng mở Dashboard danh sách insight
- **THEN** Tất cả các card insight đều được hiển thị với kích thước bằng nhau, sắp xếp thẳng hàng trong grid chuẩn, không có card nào kéo dài sang 2 cột.

#### Scenario: Display inline thumbnail or hide image container gracefully
- **WHEN** Card insight có chứa `primary_image` hợp lệ
- **THEN** Ảnh hiển thị dưới dạng thumbnail nhỏ (100px x 70px) ở phía bên phải nội dung card.

#### Scenario: Hide image container when image fails to load or is missing
- **WHEN** Card insight không có `primary_image` hoặc ảnh bị lỗi load (kích hoạt sự kiện `onError` của thẻ `<img>`)
- **THEN** Container chứa ảnh sẽ bị ẩn hoàn toàn, phần nội dung chữ bên trái sẽ tự động giãn ra lấp đầy toàn bộ không gian của card, và tuyệt đối không hiện bất kỳ icon placeholder trống nào.

---

### Requirement: Include primary_image in List API Response
Backend API danh sách `/insights` phải trả về thêm trường `primary_image` cho mỗi item trong list.

#### Scenario: API responses contain primary_image field
- **WHEN** Client gọi GET `/api/v1/insights`
- **THEN** Mỗi item trong mảng `items` của response JSON đều chứa key `primary_image`, có giá trị là URL ảnh dạng string hoặc `null`.
