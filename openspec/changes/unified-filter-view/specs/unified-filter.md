## MODIFIED Requirements

### Requirement: Thống nhất các bộ lọc trên giao diện (Unified Filter Panel)

Giao diện danh sách bản tin (`InsightList`) MUST loại bỏ thanh tab phân chia cũ (`TabBar` và `activeTab` state), thay thế bằng một giao diện hợp nhất (unified view) nơi tất cả các bộ lọc được gom chung và hiển thị đồng thời.

#### Scenario: Giao diện bộ lọc hợp nhất
- **WHEN** người dùng truy cập trang danh sách bản tin
- **THEN** thanh tab cũ MUST không hiển thị
- **THEN** hệ thống MUST hiển thị một bảng điều khiển bộ lọc hợp nhất (Unified Filter Panel) chứa tất cả các tiêu chí lọc: urgency, momentum, vietnam relevance, intelligence tier, sources, và roles
- **AND** các bộ lọc này SHALL luôn hiển thị hoặc được bố trí dạng collapsible thân thiện với di động

#### Scenario: Tích hợp ô tìm kiếm trên thanh công cụ
- **WHEN** người dùng xem thanh công cụ (toolbar) chính của danh sách bản tin
- **THEN** thanh công cụ MUST hiển thị một ô nhập liệu tìm kiếm (search box)
- **WHEN** người dùng gõ từ khóa vào ô tìm kiếm
- **THEN** danh sách bản tin SHALL được lọc tức thời theo tiêu đề hoặc từ khóa tương ứng

#### Scenario: Gửi nhiều bộ lọc đồng thời lên API
- **WHEN** người dùng chọn đồng thời nhiều tiêu chí lọc khác nhau (ví dụ: vừa chọn vai trò "DevOps" vừa chọn nguồn "arXiv")
- **THEN** ứng dụng MUST gửi tất cả các tiêu chí lọc này trong cùng một API request duy nhất tới backend
- **AND** hệ thống SHALL không reset các bộ lọc khác khi người dùng thay đổi một bộ lọc cụ thể

#### Scenario: Xóa nhanh các bộ lọc đang chọn
- **WHEN** có ít nhất một tiêu chí bộ lọc đang được kích hoạt (active)
- **THEN** Unified Filter Panel MUST hiển thị số lượng bộ lọc đang active và một nút bấm "Xóa tất cả" (Clear all) để reset nhanh toàn bộ trạng thái lọc về mặc định
