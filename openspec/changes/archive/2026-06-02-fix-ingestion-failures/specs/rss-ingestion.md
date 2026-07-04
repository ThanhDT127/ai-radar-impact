## ADDED Requirements

### Requirement: Cấu hình độ dài nội dung tối thiểu (min_content_length) theo từng nguồn tin
Hệ thống phải hỗ trợ ghi đè độ dài tối thiểu `min_content_length` từ config cụ thể của nguồn tin, thay vì luôn sử dụng cấu hình mặc định toàn cục `settings.min_content_length`.

#### Scenario: Bài viết thỏa mãn min_content_length tùy chỉnh
- **WHEN** Tiến trình cào một entry có độ dài nội dung sau chuẩn hóa là 65 ký tự từ nguồn tin có cấu hình `"min_content_length": 0`.
- **THEN** Entry vượt qua bộ lọc độ dài thành công và được lưu vào cơ sở dữ liệu.

#### Scenario: Bài viết bị bỏ qua do không đạt min_content_length tùy chỉnh
- **WHEN** Tiến trình cào một entry có độ dài nội dung sau chuẩn hóa là 5 ký tự từ nguồn tin có cấu hình `"min_content_length": 10`.
- **THEN** Entry bị bỏ qua và ghi nhận trạng thái skipped do quá ngắn.

#### Scenario: Sử dụng cấu hình min_content_length mặc định toàn cục
- **WHEN** Tiến trình cào một entry từ nguồn tin không khai báo `"min_content_length"` trong config.
- **THEN** Hệ thống sử dụng cấu hình mặc định toàn cục `settings.min_content_length` (200 ký tự) làm ngưỡng kiểm tra.
