## Why

Trong quá trình phát triển dự án AI Radar Impact, nhiều thay đổi (changes) liên quan đến cả Backend và Frontend đã được triển khai và lưu trữ (archived). Tuy nhiên, do một số thay đổi được lưu trữ với tùy chọn bỏ qua cập nhật đặc tả (`--skip-specs`) hoặc gặp lỗi cấu trúc thư mục đặc tả delta, các file đặc tả chính (`openspec/specs/insight-dashboard/spec.md` và `openspec/specs/ai-analysis/spec.md`) hiện tại đang bị thiếu và không đồng bộ với các tính năng thực tế đang chạy. 

Việc đồng bộ hóa các tài liệu đặc tả chính này là vô cùng cần thiết để đảm bảo tính nhất quán của hệ thống tài liệu BDD, giúp các đợt phát triển tiếp theo có thông tin tham chiếu chuẩn xác nhất.

## What Changes

- **Đồng bộ hóa đặc tả Frontend (`insight-dashboard`)**: Cập nhật file đặc tả chính để tích hợp các hành vi (scenarios) và yêu cầu (requirements) mới liên quan đến:
  - Bố cục đọc linh hoạt 3 chế độ (fluid-split-view)
  - Vùng tín hiệu kỹ thuật (advanced-card-layout)
  - Layout chia đôi màn hình chi tiết 50/50 (detail-split-view)
  - Thiết kế mới cho thẻ InsightCard (insight-card-redesign, optimize-insight-card)
  - Nâng cấp giao diện KPI và Tooltip (kpi-cards-upgrade, dashboard-ui-redesign)
  - Bảng điều khiển bộ lọc hợp nhất và ô tìm kiếm (unified-filter-view)
  - Tìm kiếm phía frontend (global-search-backend)
  - Thiết kế chi tiết card, viền màu, và cờ Việt Nam (ui-redesign / card-redesign)
- **Đồng bộ hóa đặc tả Backend AI (`ai-analysis`)**: Cập nhật file đặc tả chính để tích hợp các yêu cầu:
  - Tìm kiếm API backend theo từ khóa (global-search-backend)
  - Sử dụng Negative Constraints và Few-shot Prompting để tối ưu hóa văn phong tiếng Việt (dynamic-prompting-fewshot)

### Non-goals

- Không thực hiện bất kỳ thay đổi nào đối với mã nguồn (code) của backend hay frontend.
- Không thay đổi cấu trúc database hoặc API endpoints.
- Chỉ tập trung vào việc cập nhật và đồng bộ hóa tài liệu đặc tả hệ thống (`openspec/specs`).

## Capabilities

### New Capabilities

- Không có.

### Modified Capabilities

- `insight-dashboard`: Cập nhật các yêu cầu giao diện của dashboard để phản ánh đúng giao diện hiện tại.
- `ai-analysis`: Cập nhật các yêu cầu về phân tích AI và tìm kiếm bài viết ở backend.

## Impact

- **Tài liệu hệ thống**: Cập nhật các file đặc tả chính:
  - `openspec/specs/insight-dashboard/spec.md`
  - `openspec/specs/ai-analysis/spec.md`
- **Các Module bị ảnh hưởng**: M4 (AI Analysis) và M6 (Dashboard).
- **Phase áp dụng**: Phase 1 (MVP).
- **Dependencies**: Không có dependency với các Epic khác ngoài việc kế thừa các spec delta từ các thay đổi cũ.
