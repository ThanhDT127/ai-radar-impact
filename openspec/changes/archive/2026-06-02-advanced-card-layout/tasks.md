## 1. Triển khai Giao diện và Layout mới cho Card

- [x] 1.1 Sửa đổi file [InsightCard.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/components/InsightCard.tsx) để thêm khối JSX render hàng Tín hiệu Kỹ thuật (Technical Signals Row)
- [x] 1.2 Bổ sung các class CSS cần thiết trong file [card.module.css](file:///d:/Works/AI%20Radar%20Impact/frontend/src/styles/card.module.css) để định dạng và căn lề cho các badge tín hiệu kỹ thuật nằm ngang
- [x] 1.3 Cập nhật hàm `generateCardBullets` (hoặc nơi lấy mảng bullets) để cắt mảng (`slice`) giới hạn tối đa 3 dòng

## 2. Xác thực và Kiểm thử Giao diện

- [x] 2.1 Kiểm tra các bản tin có `has_code_example: true` hoặc các trường boolean khác tương ứng để đảm bảo badge hiển thị chính xác
- [x] 2.2 Đảm bảo các bản tin không có tín hiệu kỹ thuật sẽ tự động ẩn hàng tín hiệu đi mà không làm vỡ bố cục thẻ
- [x] 2.3 Kiểm tra chiều cao tổng thể của các thẻ trên grid Dashboard đảm bảo chúng cân đối và scannable hơn
