## 1. Cập nhật Component InsightCard

- [x] 1.1 Thêm tham số `displayTitle` vào hàm `generateCardBullets` trong file [InsightCard.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/components/InsightCard.tsx)
- [x] 1.2 Bổ sung điều kiện so sánh `insight.summary_short !== displayTitle` để bỏ qua việc phân tách câu từ `summary_short` vào mảng `bullets`
- [x] 1.3 Cập nhật phần gọi hàm `generateCardBullets` trong component `InsightCard` để truyền `displayTitle` làm đối số thứ hai

## 2. Kiểm thử và Xác thực

- [x] 2.1 Khởi chạy frontend cục bộ và kiểm tra một số card có tiêu đề gốc là tiếng Anh để xác nhận không còn hiện tượng lặp lại nội dung `summary_short` ở phần bullets
- [x] 2.2 Xác nhận các card có tiêu đề tiếng Việt vẫn sinh ra bullets từ `summary_short` và hiển thị đầy đủ thông tin bình thường
- [x] 2.3 Đảm bảo ứng dụng chạy mượt mà, không gặp lỗi runtime hay typescript compile errors
