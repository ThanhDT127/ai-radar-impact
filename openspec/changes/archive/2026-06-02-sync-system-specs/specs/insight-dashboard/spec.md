## MODIFIED Requirements

### Requirement: Tách cấu trúc thẻ InsightCard và hiển thị Technical Signals dạng Badges

Giao diện thẻ `InsightCard` MUST hỗ trợ hiển thị nổi bật các thuộc tính kỹ thuật thực hành (Technical Signals) ở một vùng riêng biệt và giới hạn số lượng bullet points ở phần nội dung tóm tắt để giữ thẻ tinh gọn.

#### Scenario: Hiển thị các chỉ số Technical Signals dạng Badges
- **WHEN** một `Insight` có ít nhất một trong các thuộc tính boolean (`has_code_example`, `has_benchmark`, `has_api_change`, `has_security_patch`) là `true`
- **THEN** thẻ `InsightCard` MUST hiển thị một hàng "Tín hiệu Kỹ thuật" nằm ngay dưới tiêu đề
- **AND** các badges tương ứng với giá trị `true` SHALL được render rõ ràng:
  * `has_code_example` ➔ `💻 Có code mẫu`
  * `has_benchmark` ➔ `📊 Có benchmark`
  * `has_api_change` ➔ `🔗 Thay đổi API`
  * `has_security_patch` ➔ `🛡️ Bảo mật`

#### Scenario: Không có tín hiệu kỹ thuật nào
- **WHEN** một `Insight` có cả bốn thuộc tính boolean trên đều là `false`
- **THEN** hàng "Tín hiệu Kỹ thuật" trên thẻ MUST tự động ẩn đi và không render bất kỳ khoảng trống thừa nào

#### Scenario: Giới hạn tối đa 3 bullet points
- **WHEN** thẻ `InsightCard` hiển thị danh sách các gạch đầu dòng tóm tắt (`bullets`)
- **THEN** số lượng bullets hiển thị trên thẻ MUST chỉ có tối đa 3 dòng (thay vì 5 dòng như trước) để đảm bảo thẻ gọn gàng

---

### Requirement: Điều khiển bố cục đọc linh hoạt (Fluid Split-View Controls)

Trang chi tiết Insight MUST tích hợp bộ điều khiển cho phép người dùng chuyển đổi giữa 3 chế độ đọc: Split View (50/50), Focus AI (80/20), Focus Original (20/80) và tự động lưu lựa chọn này vào bộ nhớ trình duyệt (`localStorage`).

#### Scenario: Giao diện bộ điều khiển chế độ đọc
- **WHEN** người dùng mở trang chi tiết Insight
- **THEN** trang chi tiết MUST hiển thị một toolbar nhỏ chứa 3 nút chuyển chế độ ở đầu trang: "Đọc song song" (Split), "Phân tích chi tiết" (Focus AI), và "Bài viết gốc" (Focus Original)
- **AND** chế độ được chọn mặc định từ đầu SHALL là chế độ lưu trong `localStorage` (hoặc fallback về 'split' nếu chưa lưu)

#### Scenario: Chuyển sang chế độ Focus AI (Tập trung phân tích)
- **WHEN** người dùng click vào nút "Phân tích chi tiết" (Focus AI)
- **THEN** cột phân tích AI bên trái MUST mở rộng chiếm 80% chiều rộng màn hình
- **AND** cột bài gốc bên phải MUST thu hẹp còn 20%
- **AND** cột bài gốc bên phải MUST ẩn nội dung iframe đi, thay thế bằng tiêu đề bài gốc và nút bấm mở rộng nhanh "Bài viết gốc ◀"

#### Scenario: Chuyển sang chế độ Focus Original (Tập trung bài gốc)
- **WHEN** người dùng click vào nút "Bài viết gốc" (Focus Original)
- **THEN** cột bài gốc bên phải MUST mở rộng chiếm 80% chiều rộng màn hình
- **AND** cột phân tích AI bên trái MUST thu hẹp còn 20%
- **AND** cột phân tích AI bên trái MUST ẩn các mục văn bản dài (bullets, khuyến nghị, rủi ro) và chỉ giữ lại tiêu đề kèm nút bấm mở rộng "Phân tích chi tiết ▶"

#### Scenario: Hiệu ứng chuyển cảnh mượt mà và chống scroll jump
- **WHEN** người dùng chuyển đổi giữa bất kỳ chế độ nào trong 3 chế độ đọc
- **THEN** kích thước các cột MUST thay đổi thông qua một hiệu ứng chuyển cảnh mượt mà bằng CSS (transition) với thời gian chuyển tiếp từ 0.2s đến 0.4s
- **AND** vị trí cuộn màn hình (`window.scrollY`) SHALL được khôi phục chính xác để tránh hiện tượng nhảy trang lên đầu.

---

### Requirement: Layout chia đôi trang chi tiết (Detail Split-View)

Trang chi tiết Insight (`InsightDetail`) MUST hiển thị dạng split-view chia đôi tỉ lệ 50/50 trên màn hình lớn (>= 1024px): panel bên trái hiển thị nội dung phân tích tóm tắt bằng tiếng Việt, panel bên phải hiển thị bài viết gốc bằng tiếng Anh.

#### Scenario: Hiển thị trên màn hình Desktop
- **WHEN** người dùng truy cập trang chi tiết với chiều rộng màn hình >= 1024px
- **THEN** trang chi tiết MUST hiển thị dạng split-view chia đôi 50/50
- **THEN** panel bên trái hiển thị đầy đủ thông tin phân tích của AI (title, tags, bullets, khuyến nghị, rủi ro, scoring)
- **THEN** panel bên phải hiển thị bài viết gốc nhúng trong iframe thông qua `source_url`

#### Scenario: Iframe bị chặn hoặc lỗi tải trang
- **WHEN** iframe không thể hiển thị nội dung (do lỗi mạng hoặc do chính sách bảo mật X-Frame-Options)
- **THEN** panel bên phải SHALL hiển thị một giao diện fallback thay thế
- **THEN** giao diện fallback MUST bao gồm tiêu đề bài viết gốc và một nút bấm nổi bật "Mở bài gốc trong tab mới"

#### Scenario: Hiển thị trên thiết bị di động
- **WHEN** người dùng truy cập trang chi tiết trên thiết bị di động hoặc máy tính bảng có màn hình < 1024px
- **THEN** bố cục split-view MUST tự động chuyển sang dạng xếp chồng dọc (stack vertical)
- **THEN** panel phân tích AI hiển thị ở phía trên và panel bài viết gốc hiển thị ở phía dưới

#### Scenario: Hiển thị verification badge của AI
- **WHEN** panel phân tích AI tải thành công
- **THEN** panel trái MUST hiển thị verification badge "🤖 Phân tích bởi Gemini AI"
- **THEN** badge này SHALL hiển thị rõ ràng độ tin cậy (confidence) của mô hình AI dưới dạng phần trăm (ví dụ: "Confidence: 85%")

---

### Requirement: Tái cấu trúc giao diện thẻ InsightCard

Thẻ thông tin `InsightCard` MUST được thiết kế lại theo hướng tinh gọn và dễ quét (scannable), chuyển từ cấu trúc nặng văn bản (text-heavy) sang cấu trúc phân tầng thông tin rõ ràng.

#### Scenario: Cấu trúc các dòng thông tin trên thẻ
- **WHEN** thẻ `InsightCard` được hiển thị trên dashboard
- **THEN** Row 1 ở đầu card MUST hiển thị nhãn phân tầng (`intelligence_tier`) và thời gian đăng bài (`relative_time`)
- **THEN** Row 2 MUST hiển thị các nhãn chủ đề (`topic tags`) và loại sự kiện (`event_type`)
- **THEN** Title block MUST hiển thị tên nguồn bài viết (`source_name`), tiêu đề tiếng Việt (dạng bold) và tiêu đề phụ tiếng Anh (nếu có và khác tiêu đề tiếng Việt)

#### Scenario: Danh sách tóm tắt dạng bullet points
- **WHEN** thẻ render phần nội dung tóm tắt chính (body)
- **THEN** thẻ MUST hiển thị tối đa 5 gạch đầu dòng (`bullets`) thay thế cho các khối văn bản "Điểm chính" trước đây
- **AND** các gạch đầu dòng này SHALL được lấy từ các trường dữ liệu `signal`, `so_what`, `why_it_matters` và phân tách từ `summary_short`

#### Scenario: Footer chứa các chỉ số gọn gàng (Compact Footer)
- **WHEN** thẻ hiển thị phần chân trang (footer)
- **THEN** các chỉ số đo lường (actionability score, trust score, adoption ring, momentum) MUST được sắp xếp nằm ngang trên một dòng đơn giản
- **AND** các chỉ số này SHALL được ngăn cách bởi dấu chấm trung tâm (`·`) rõ ràng

---

### Requirement: Nâng cấp giao diện hiển thị các thẻ KPI thống kê

Các thẻ KPI thống kê trên đầu trang Dashboard (`KPISummary`) MUST được bổ sung thông tin ngữ cảnh, biểu tượng giải thích và phối màu trực quan để người dùng hiểu rõ ý nghĩa các chỉ số.

#### Scenario: Bố cục đầy đủ thông tin của thẻ KPI
- **WHEN** các thẻ KPI được hiển thị trên dashboard
- **THEN** mỗi thẻ KPI MUST hiển thị 4 thành phần chính: tiêu đề nhãn (label), biểu tượng tooltip ⓘ, số lượng tổng lớn, và chú thích phụ (subtitle) luôn hiển thị bên dưới
- **AND** tiêu đề nhãn SHALL được cập nhật rõ nghĩa hơn: "Tổng bản tin", "Ảnh hưởng cao", "Cơ hội hành động", "Nguồn hoạt động"

#### Scenario: Hiển thị tooltip giải thích chi tiết khi hover
- **WHEN** người dùng di chuột (hover) vào biểu tượng ⓘ bên cạnh nhãn của bất kỳ thẻ KPI nào
- **THEN** hệ thống MUST hiển thị một khung thông tin giải thích (tooltip) chi tiết về nguồn gốc và cách tính của chỉ số đó sử dụng component `<Tooltip>` chung

#### Scenario: Phối màu cảnh báo trực quan theo ngữ cảnh (Semantic Colors)
- **WHEN** thẻ KPI "Ảnh hưởng cao" được hiển thị
- **THEN** con số thống kê hoặc nền phụ của thẻ MUST sử dụng màu đỏ hoặc cam nổi bật để cảnh báo
- **WHEN** thẻ KPI "Cơ hội hành động" được hiển thị
- **THEN** con số thống kê hoặc nền phụ của thẻ MUST sử dụng màu xanh lá cây để biểu thị tín hiệu cơ hội phát triển

---

### Requirement: Thống nhất các bộ lọc trên giao diện (Unified Filter Panel)

Giao diện danh sách bản tin (`InsightList`) MUST loại bỏ thanh tab phân chia cũ, thay thế bằng một giao diện hợp nhất (unified view) nơi tất cả các bộ lọc được gom chung và hiển thị đồng thời.

#### Scenario: Giao diện bộ lọc hợp nhất
- **WHEN** người dùng truy cập trang danh sách bản tin
- **THEN** thanh tab cũ MUST không hiển thị
- **THEN** hệ thống MUST hiển thị một bảng điều khiển bộ lọc hợp nhất (Unified Filter Panel) chứa tất cả các tiêu chí lọc: urgency, momentum, vietnam relevance, intelligence tier, sources, và roles
- **AND** các bộ lọc này SHALL luôn hiển thị hoặc được bố trí dạng collapsible thân thiện với di động

#### Scenario: Gửi nhiều bộ lọc đồng thời lên API
- **WHEN** người dùng chọn đồng thời nhiều tiêu chí lọc khác nhau
- **THEN** ứng dụng MUST gửi tất cả các tiêu chí lọc này trong cùng một API request duy nhất tới backend
- **AND** hệ thống SHALL không reset các bộ lọc khác khi người dùng thay đổi một bộ lọc cụ thể

#### Scenario: Xóa nhanh các bộ lọc đang chọn
- **WHEN** có ít nhất một tiêu chí bộ lọc đang được kích hoạt (active)
- **THEN** Unified Filter Panel MUST hiển thị số lượng bộ lọc đang active và một nút bấm "Xóa tất cả" (Clear all) để reset nhanh toàn bộ trạng thái lọc về mặc định

---

### Requirement: Tối ưu hiển thị các gạch đầu dòng (bullets) trên InsightCard

Để tránh trùng lặp thông tin hiển thị trên giao diện thẻ, hàm `generateCardBullets` trong `InsightCard.tsx` MUST nhận thêm tham số `displayTitle` và SHALL tự động loại bỏ nội dung từ `summary_short` ra khỏi danh sách `bullets` nếu `summary_short` được dùng làm tiêu đề hiển thị (`displayTitle`).

#### Scenario: Tiêu đề hiển thị trùng với summary_short
- **WHEN** một `Insight` có tiêu đề gốc bằng tiếng Anh và trường `summary_short` được chọn làm tiêu đề hiển thị `displayTitle`
- **THEN** danh sách `bullets` hiển thị trên `InsightCard` MUST không chứa các câu được tách từ `summary_short` để tránh trùng lặp
- **AND** danh sách `bullets` vẫn hiển thị tối đa 5 phần tử chất lượng được lấy từ các trường `signal`, `so_what` và `why_it_matters`

---

### Requirement: Tích hợp ô tìm kiếm toàn cục trên Toolbar (search-insights-frontend)

Giao diện Dashboard chính MUST hiển thị ô nhập tìm kiếm toàn cục trên Toolbar, hỗ trợ gõ từ khóa tìm kiếm và tự động cập nhật URL.

#### Scenario: Nhập từ khóa tìm kiếm
- **WHEN** Người dùng nhập từ khóa vào ô tìm kiếm trên Toolbar
- **THEN** Sau 300ms, URL được cập nhật thành `/?search=keyword` và danh sách bài viết được làm mới tương ứng với kết quả từ Backend API.

#### Scenario: Xóa từ khóa tìm kiếm
- **WHEN** Người dùng xóa nội dung trong ô tìm kiếm hoặc click vào dấu "×" trên filter chip tìm kiếm
- **THEN** URL xóa bỏ tham số `search` và danh sách bài viết được khôi phục về trạng thái không lọc.

---

### Requirement: Badge System Cleanup và Shimmer Loading

Toàn bộ badge (Urgency, Impact, Role, Tier, Momentum) MUST theo design system mới, có glassmorphism style nhẹ, labels rõ ràng, và skeleton loading MUST có shimmer animation premium.

#### Scenario: Badge labels không mơ hồ
- **WHEN** UrgencyBadge hoặc ImpactBadge render level "Trung bình"
- **THEN** MUST hiển thị prefix: "Cấp thiết: Trung bình" hoặc "Ảnh hưởng: Trung bình" — không dùng "Trung bình" standalone

#### Scenario: Badge glassmorphism style
- **WHEN** bất kỳ badge render
- **THEN** MUST có: `backdrop-filter: blur(8px)`, semi-transparent background, subtle border, và border-radius 8px

#### Scenario: Shimmer skeleton khi loading
- **WHEN** data đang fetch
- **THEN** MUST hiển thị skeleton cards với shimmer animation (gradient wave effect), featured skeleton card lớn hơn standard skeleton cards


---

### Requirement: Thiết kế chi tiết card (ui-redesign)

Thẻ `InsightCard` MUST có các thuộc tính thiết kế nâng cao để tăng khả năng quét và nhận diện trực quan.

#### Scenario: Màu viền trái theo Intelligence Tier
- **WHEN** card render với `intelligence_tier` tương ứng
- **THEN** viền trái card (4px width) MUST sử dụng màu: Tactical ➔ đỏ (`--color-danger`), Operational ➔ cam (`--color-warning`), Strategic ➔ tím (`--color-strategic`), Informational ➔ xám (`--color-neutral`).

#### Scenario: Thanh urgency top strip
- **WHEN** card render với `urgency` là "critical" hoặc "high"
- **THEN** hiển thị một thanh gradient mỏng (3px height) ở top edge của card.

#### Scenario: Cờ Việt Nam cho mức liên quan cao
- **WHEN** insight có `vietnam_relevance` là "high"
- **THEN** hiển thị icon cờ Việt Nam (🇻🇳) ở góc thẻ.
