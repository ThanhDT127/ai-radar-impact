# chat-web-widget

## ADDED Requirements

### Requirement: Widget chat nổi trên mọi trang
Frontend SHALL hiển thị nút mở chat ở góc phải dưới trên mọi trang của dashboard. Bấm nút SHALL mở panel chat (~380px trên desktop); panel SHALL đóng/mở được mà không mất nội dung hội thoại trong phiên. Widget SHALL không tự động mở.

#### Scenario: Mở và đóng widget
- **WHEN** người dùng bấm nút chat ở góc màn hình
- **THEN** panel chat mở; bấm đóng thì panel ẩn nhưng hội thoại còn nguyên khi mở lại trong cùng phiên

#### Scenario: Không che thao tác chính
- **WHEN** panel chat đang mở trên desktop
- **THEN** người dùng vẫn cuộn và thao tác được với danh sách/chi tiết insight phía sau

### Requirement: Context chip theo insight đang mở
Khi người dùng đang ở trang chi tiết một insight (`/insights/:id`), widget SHALL tự gắn context chip hiển thị title insight đó và gửi `insight_id` kèm câu hỏi (chế độ B). Người dùng SHALL bỏ được chip (✕) để chuyển sang hỏi toàn cục. Khi rời trang chi tiết, widget SHALL trở về chế độ toàn cục.

#### Scenario: Tự gắn context khi xem detail
- **WHEN** người dùng mở chi tiết insight rồi mở widget và đặt câu hỏi
- **THEN** request gửi kèm `insight_id` của insight đang xem và chip hiển thị title insight

#### Scenario: Bỏ context chip
- **WHEN** người dùng bấm ✕ trên context chip
- **THEN** câu hỏi tiếp theo gửi không kèm `insight_id` (chế độ toàn cục)

#### Scenario: Chuyển insight đang xem
- **WHEN** người dùng chuyển sang xem insight khác trong khi widget mở
- **THEN** context chip cập nhật theo insight mới

#### Scenario: Quay về danh sách
- **WHEN** người dùng rời trang chi tiết về danh sách trong khi widget mở
- **THEN** context chip biến mất và câu hỏi tiếp theo chạy chế độ toàn cục

### Requirement: Render citation thành link
Câu trả lời của bot SHALL hiển thị citations dưới dạng link; bấm citation SHALL điều hướng đến chi tiết insight tương ứng trong dashboard.

#### Scenario: Bấm citation
- **WHEN** bot trả lời kèm citation
- **THEN** citation hiển thị title insight dạng link, bấm vào mở chi tiết insight đó

### Requirement: Trạng thái chờ và lỗi
Widget SHALL hiển thị trạng thái đang xử lý trong khi chờ trả lời, và thông báo lỗi tiếng Việt kèm khả năng hỏi lại khi API lỗi hoặc hết quota (429).

#### Scenario: Hết quota chat
- **WHEN** API trả về 429
- **THEN** widget hiển thị thông báo hết lượt hỏi trong ngày bằng tiếng Việt, không mất hội thoại

#### Scenario: Lỗi mạng
- **WHEN** request chat thất bại vì lỗi mạng/server
- **THEN** widget hiển thị lỗi và cho phép gửi lại câu hỏi vừa nhập
