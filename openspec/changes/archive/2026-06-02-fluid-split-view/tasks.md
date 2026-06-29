## 1. Triển khai Logic State và Toolbar trên Giao diện

- [x] 1.1 Thêm state `viewMode` và xây dựng giao diện Toolbar chọn chế độ đọc trong file [InsightDetail.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/pages/InsightDetail.tsx)
- [x] 1.2 Viết logic đọc/ghi trạng thái `viewMode` vào `localStorage` của trình duyệt để lưu tùy chọn của người dùng

## 2. Cấu hình CSS Grid Động và Hiệu ứng Chuyển cảnh

- [x] 2.1 Định nghĩa các CSS classes mới (`layoutSplit`, `layoutFocusAI`, `layoutFocusOriginal`) trong file [insights.module.css](file:///d:/Works/AI%20Radar%20Impact/frontend/src/styles/insights.module.css)
- [x] 2.2 Bổ sung thuộc tính `transition` trên `grid-template-columns` để hiệu ứng co dãn cột diễn ra mượt mà

## 3. Xử lý Trạng thái Ẩn/Hiện Nội dung khi Thu hẹp Cột (Sidebar Mode)

- [x] 3.1 Cập nhật cột phải: Ẩn iframe (bằng CSS) và hiển thị nút mở rộng nhanh khi `viewMode === 'focus-ai'`
- [x] 3.2 Cập nhật cột trái: Ẩn các đoạn văn bản phân tích dài (bullets, khuyến nghị, rủi ro) khi `viewMode === 'focus-original'`

## 4. Kiểm thử và Cân chỉnh UI

- [x] 4.1 Kiểm tra sự mượt mà của hiệu ứng chuyển cảnh khi nhấp chuột chuyển đổi nhanh giữa 3 chế độ trên các kích thước màn hình desktop khác nhau
- [x] 4.2 Kiểm tra xem trạng thái chế độ đọc có được khôi phục chính xác từ `localStorage` sau khi F5 tải lại trang hay không
