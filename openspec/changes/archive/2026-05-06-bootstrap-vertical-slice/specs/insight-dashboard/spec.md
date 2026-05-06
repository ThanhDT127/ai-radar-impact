## ADDED Requirements

### Requirement: Trang danh sách Insights

React page hiển thị danh sách insight dưới dạng cards, fetch từ backend API.

#### Scenario: Hiển thị danh sách insight
- **WHEN** user truy cập trang chủ (`/`)
- **THEN** hiển thị danh sách insight cards, mỗi card gồm: title, summary_short, topics (tags), impact_label (badge màu), event_type, thời gian (relative: "2 giờ trước")

#### Scenario: Loading state
- **WHEN** đang fetch dữ liệu từ API
- **THEN** hiển thị skeleton loading (không blank screen)

#### Scenario: Empty state
- **WHEN** API trả về 0 insights
- **THEN** hiển thị message "Chưa có insight nào. Chạy ingestion để bắt đầu thu thập dữ liệu."

#### Scenario: Error state
- **WHEN** API call thất bại (network error, 500)
- **THEN** hiển thị error message với nút "Thử lại"

### Requirement: Trang chi tiết Insight

Khi click vào 1 insight card, navigate tới trang chi tiết.

#### Scenario: Hiển thị chi tiết
- **WHEN** user click vào 1 insight card
- **THEN** navigate tới `/insights/:id` và hiển thị: title, summary_medium (full), topics, event_type, nature, trust_score, impact_label, source_url (link clickable mở tab mới), created_at

#### Scenario: Link về nguồn gốc
- **WHEN** user click vào source_url trên trang detail
- **THEN** mở link gốc (GitHub Changelog post) trong tab mới

#### Scenario: Insight không tồn tại
- **WHEN** user truy cập `/insights/:id` với id không hợp lệ
- **THEN** hiển thị "Insight không tìm thấy" với link quay về trang chủ

### Requirement: Impact label màu sắc

Impact label phải có visual indicator rõ ràng bằng màu.

#### Scenario: Màu theo impact level
- **WHEN** insight card hoặc detail hiển thị impact_label
- **THEN** badge dùng màu: Critical → đỏ, High → cam, Medium → vàng, Low → xanh lá, Watch → xám

### Requirement: Responsive và hiệu năng

Dashboard phải responsive và load nhanh.

#### Scenario: Mobile responsive
- **WHEN** user mở trang trên màn hình < 768px
- **THEN** cards chuyển sang layout 1 cột, text vẫn đọc được, không bị cắt

#### Scenario: Pagination UI
- **WHEN** có nhiều hơn 20 insights
- **THEN** hiển thị pagination controls (Previous/Next) ở cuối danh sách
