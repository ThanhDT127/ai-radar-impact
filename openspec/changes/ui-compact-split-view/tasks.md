## 1. Backend Integration

- [x] 1.1 Thêm trường primary_image vào Pydantic schema InsightListItem trong backend/app/schemas/insight.py
- [x] 1.2 Kiểm tra response API GET /api/v1/insights để đảm bảo trường primary_image đã xuất hiện và có dữ liệu chính xác

## 2. List Page & Card Refactoring

- [x] 2.1 Cập nhật InsightCard.tsx: Loại bỏ logic render featured card, đưa ảnh thành thumbnail inline nhỏ bên phải text
- [x] 2.2 Tích hợp onError event handler vào thẻ img trong InsightCard.tsx để tự động ẩn container ảnh khi load lỗi
- [x] 2.3 Cập nhật InsightList.tsx: Loại bỏ class/featured logic, đảm bảo tất cả cards hiển thị đồng đều trên grid
- [x] 2.4 Điều chỉnh CSS trong insights.module.css để hỗ trợ layout card đồng nhất, thumbnail inline bên phải, và tự động co giãn phần chữ khi không có ảnh

## 3. Detail Page & Split View Refactoring

- [x] 3.1 Cập nhật cấu trúc Header trong InsightDetail.tsx: Loại bỏ hero background image, đưa ảnh chính thành thumbnail flex cạnh title
- [x] 3.2 Đưa phần core summary (so_what) lên vị trí nổi bật ngay dưới tiêu đề trong InsightDetail.tsx
- [x] 3.3 Thiết kế dải Metadata Ribbon ngang trong InsightDetail.tsx, gộp gọn 6 cards thông tin cũ (scores, general info, indicators, timeline)
- [x] 3.4 Triển khai layout Split View 50/50 trong InsightDetail.tsx: Cột trái chứa bản dịch và phân tích tiếng Việt, cột phải chứa bài viết gốc tiếng Anh
- [x] 3.5 Tích hợp logic scroll độc lập cho 2 cột và auto-fallback co dãn 100% cột trái nếu bài viết gốc trống
- [x] 3.6 Cập nhật CSS trong insights.module.css để hỗ trợ dải Ribbon ngang và Grid Split View 50/50 scroll độc lập

## 4. Verification & Testing

- [x] 4.1 Khởi động và kiểm tra toàn bộ dashboard tại local để đảm bảo không bị lỗi biên dịch TypeScript
- [x] 4.2 Kiểm chứng trực quan giao diện danh sách: các card đồng đều, ảnh thumbnail bên phải load mượt, bài viết không ảnh hiển thị sạch đẹp
- [x] 4.3 Kiểm chứng trực quan giao diện trang chi tiết: dải metadata ribbon gọn gàng, split view song ngữ scroll mượt mà, bài viết gốc hiển thị đầy đủ
