## ADDED Requirements

### Requirement: Login-wall Detection
Sau khi load trang MXH, connector MUST phát hiện trường hợp bị chặn bởi login-wall (redirect sang trang đăng nhập hoặc xuất hiện login form đặc trưng theo domain: `linkedin.com/authwall`, `linkedin.com/login`, `x.com/i/flow/login`). Khi phát hiện, connector MUST log ERROR kèm hướng dẫn khắc phục (chạy lại quy trình codegen) và trả về `[]` — MUST NOT trích nội dung trang login làm bài viết.

#### Scenario: Cookie hết hạn ở LinkedIn
- **WHEN** phiên trong `cookie_file` đã bị LinkedIn hủy và trang feed redirect sang `/authwall`
- **THEN** connector log ERROR nêu rõ nguồn nào chết phiên + cách tạo lại session, trả `[]`, không tạo document rác từ trang login

#### Scenario: Thiếu file cookie ngay từ đầu
- **WHEN** `cookie_file` được khai trong config nhưng file không tồn tại
- **THEN** connector log WARNING nêu đường dẫn thiếu và vẫn thử fetch; nếu sau đó dính login-wall thì xử lý như scenario trên (không âm thầm trả 0 bài không lý do)

### Requirement: Sliding Session Refresh
Sau một phiên fetch thành công (trích được ≥ 1 entry và không dính login-wall), connector MUST lưu lại `storage_state` hiện tại của context ghi đè vào `cookie_file` (ghi atomic: file tạm + rename), để cookie được server gia hạn liên tục và phiên không bao giờ hết hạn khi được dùng đều đặn.

#### Scenario: Gia hạn cookie sau phiên thành công
- **WHEN** fetch một nguồn LinkedIn hoàn tất với ≥ 1 entry và không có login-wall
- **THEN** `cookie_file` được ghi đè bằng storage_state mới nhất; lần cào kế tiếp nạp cookie đã gia hạn

#### Scenario: Không ghi đè khi phiên thất bại
- **WHEN** fetch trả 0 entry hoặc dính login-wall
- **THEN** `cookie_file` giữ nguyên, không bị ghi đè bởi trạng thái phiên hỏng

### Requirement: Nguồn MXH yêu cầu đăng nhập phải khai báo cookie_file
Mọi nguồn MXH thuộc platform yêu cầu đăng nhập để xem nội dung (X, LinkedIn) MUST khai báo `cookie_file` trong `source.config`, trỏ tới file storage_state trong `/secrets/states/`.

#### Scenario: Nguồn X có cookie config
- **WHEN** seed sources chạy xong
- **THEN** các nguồn X (OpenAI, Anthropic, Project Zero, Kelsey Hightower) có `config.cookie_file = "/secrets/states/x_state.json"`; các nguồn LinkedIn giữ `/secrets/states/linkedin_state.json`

## MODIFIED Requirements

### Requirement: Session Cookies Injection
Hệ thống MUST hỗ trợ load trạng thái đăng nhập hợp lệ để vượt rào truy cập ẩn danh (Login Wall) của LinkedIn/X. Việc nạp session là bước đầu của vòng đời session đầy đủ: nạp → phát hiện login-wall → gia hạn sau phiên thành công (xem các requirement Login-wall Detection và Sliding Session Refresh).

#### Scenario: Cào trang yêu cầu đăng nhập
- **WHEN** config của Source chứa đường dẫn hợp lệ trong `cookie_file`
- **THEN** Playwright tạo Context trình duyệt với `storage_state` nạp từ file JSON đó, cho phép truy cập Feed dưới tư cách User hợp lệ đã login trước đó

#### Scenario: Khởi tạo session lần đầu
- **WHEN** người vận hành chạy `playwright codegen --save-storage=secrets/states/<platform>_state.json <login-url>` từ thư mục gốc repo và đăng nhập tay rồi đóng trình duyệt
- **THEN** file storage_state xuất hiện đúng vị trí mount vào container tại `/secrets/states/`, connector nạp được ở lần cào kế tiếp mà không cần restart backend
