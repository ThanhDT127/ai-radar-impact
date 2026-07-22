## ADDED Requirements

### Requirement: Gửi tin qua Gmail bằng tài khoản chung
Hệ thống SHALL cung cấp `EmailAdapter` implement `ChannelAdapter` với `channel_type = "email"`, đăng
ký vào `ChannelRegistry` để `scheduler` lấy được qua `DELIVERY_CHANNEL`. Adapter SHALL gửi qua SMTP
(`SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`) bằng App Password đọc từ env — credential
SHALL KHÔNG nằm trong repo.

Mỗi người nhận SHALL nhận một email riêng với đúng một địa chỉ ở `To:`; hệ thống SHALL KHÔNG gửi
hàng loạt bằng BCC (nội dung cá nhân hoá theo vai trò, và BCC làm tăng khả năng bị xếp spam).

Email SHALL là `multipart/alternative` gồm cả `text/plain` và `text/html`, kèm header
`List-Unsubscribe` và `List-Unsubscribe-Post: List-Unsubscribe=One-Click`.

Khi gửi lỗi (SMTP từ chối, mất kết nối), adapter SHALL trả kết quả thất bại và hệ thống SHALL KHÔNG
ghi `delivery_log` cho lần đó, để chu kỳ sau gửi lại.

#### Scenario: Gửi thành công một bản tin
- **WHEN** engine gọi `adapter.send()` với địa chỉ hợp lệ và nội dung bản tin
- **THEN** một email tới đúng địa chỉ đó, có cả phần text và phần HTML, `From` là `EMAIL_FROM`, và `delivery_log` được ghi

#### Scenario: SMTP lỗi giữa chừng
- **WHEN** SMTP trả lỗi khi gửi cho một người nhận
- **THEN** không có `delivery_log` nào được ghi cho người đó, các người nhận còn lại vẫn được gửi, và chu kỳ sau tin đó được gửi lại

#### Scenario: Nhiều người nhận
- **WHEN** có 5 subscriber active đủ điều kiện nhận bản tin
- **THEN** hệ thống gửi 5 email riêng biệt, mỗi email chỉ chứa địa chỉ của một người ở `To:`, không dùng BCC

### Requirement: Định danh người nhận bằng địa chỉ email
Bảng `subscribers` SHALL khoá chính bằng `id UUID` và định danh người nhận bằng cột `email`
(UNIQUE, lưu dạng lowercase đã normalize). Cột `chat_id` của Telegram SHALL bị loại bỏ.

`roles` SHALL là tập con của `ALLOWED_ROLES` (9 vai trò trong `app/ai/prompts.py`) — giá trị ngoài
tập đóng SHALL bị từ chối. Mỗi subscriber SHALL có `unsubscribe_token` bí mật sinh tự động lúc tạo.

#### Scenario: Email trùng khác hoa thường
- **WHEN** đã có `an@rangdong.vn` và người dùng thêm `An@Rangdong.vn`
- **THEN** hệ thống từ chối vì trùng, không tạo bản ghi thứ hai

#### Scenario: Vai trò ngoài tập đóng
- **WHEN** tạo subscriber với `roles = ["Marketing"]` (không thuộc `ALLOWED_ROLES`)
- **THEN** API trả lỗi validation và không tạo bản ghi

#### Scenario: Token hủy nhận sinh tự động
- **WHEN** một subscriber được tạo qua API
- **THEN** bản ghi có `unsubscribe_token` không rỗng và khác token của mọi subscriber khác

### Requirement: Quản lý người nhận qua dashboard
Hệ thống SHALL cung cấp REST CRUD tại `/api/v1/subscribers` (liệt kê, tạo, sửa `roles`/`active`,
xoá) và một tab **"Người nhận"** trên dashboard dùng các endpoint đó. Nhãn vai trò hiển thị SHALL
dùng lại `ROLE_DISPLAY_LABEL` trong `components/RoleBadge.tsx` để không lệch taxonomy.

Ở MVP các endpoint này SHALL KHÔNG yêu cầu xác thực.

#### Scenario: Thêm người nhận mới
- **WHEN** người dùng nhập email + chọn vai trò `[AI Engineer, Security]` trong tab "Người nhận" và lưu
- **THEN** bản ghi xuất hiện trong danh sách và người đó nằm trong danh sách nhận của kỳ bản tin kế tiếp

#### Scenario: Tạm dừng nhận tin
- **WHEN** người dùng tắt `active` của một người nhận
- **THEN** người đó không nhận bản tin kỳ kế tiếp, bản ghi vẫn còn trong danh sách

#### Scenario: Người nhận chưa chọn vai trò nào
- **WHEN** một subscriber có `roles` rỗng
- **THEN** người đó không nhận bản tin nào (không có vai trò để lọc nội dung)

### Requirement: Hủy nhận từ trong email
Mọi email gửi đi SHALL chứa link hủy nhận dựng từ `unsubscribe_token`, trỏ tới
`PUBLIC_API_BASE_URL` (gốc của backend), KHÔNG phải `DASHBOARD_BASE_URL`.

`GET` link SHALL trả trang xác nhận tối giản; `POST` cùng đường dẫn SHALL đặt `active = false` và
trả 200 — bản `POST` phục vụ one-click unsubscribe của Gmail. Hệ thống SHALL KHÔNG xoá bản ghi khi
hủy nhận.

#### Scenario: Bấm link hủy nhận
- **WHEN** người nhận mở link hủy nhận trong email và xác nhận
- **THEN** `active` của họ thành `false`, bản ghi vẫn còn, và họ không nhận bản tin kỳ sau

#### Scenario: Token sai
- **WHEN** truy cập link hủy nhận với token không tồn tại
- **THEN** hệ thống trả 404 và không thay đổi bản ghi nào

### Requirement: Email đọc được trên Gmail và Outlook
Phần HTML SHALL dùng CSS inline và layout dạng `<table>` — SHALL KHÔNG dựa vào `<style>` ngoài,
flexbox hay grid (các client email không hỗ trợ). Phần `text/plain` SHALL chứa đủ nội dung để đọc
độc lập khi client chặn HTML. Link tới chi tiết insight SHALL dùng `DASHBOARD_BASE_URL`.

#### Scenario: Client chặn HTML
- **WHEN** người nhận dùng client chỉ hiển thị plain-text
- **THEN** họ vẫn đọc được tiêu đề, signal và link dashboard của từng tin trong bản tin

### Requirement: Link trong email phải phân giải được từ máy người nhận
`DASHBOARD_BASE_URL` và `PUBLIC_API_BASE_URL` SHALL trỏ tới địa chỉ **công khai phân giải được** ở
môi trường thật. Giá trị mặc định `http://localhost:5173` và `http://localhost:8000` chỉ dùng cho
phát triển: người nhận mở email trên máy khác sẽ bấm vào một link chết, và **mọi** link trong email
(đọc chi tiết lẫn hủy nhận) đều rơi vào tình trạng đó.

Ngoài chuyện không bấm được, link không phân giải được còn là **tín hiệu spam mạnh**. Đo thật ngày
21/07/2026: bản tin gửi từ tài khoản `@gmail.com` cá nhân với toàn bộ link trỏ `localhost` rơi vào
Spam của Gmail dù nội dung, header và xác thực SMTP đều đúng.

Đây là điều kiện triển khai, KHÔNG sửa được bằng cách chỉnh template hay câu chữ. Hai điều kiện còn
lại để vào được Inbox: gửi từ tài khoản thuộc **domain công ty** (DKIM/DMARC gắn domain thay vì tài
khoản cá nhân), và người nhận đánh dấu "Không phải thư rác" ở những email đầu tiên.

#### Scenario: Triển khai thật
- **WHEN** hệ thống chạy ở môi trường thật và gửi bản tin
- **THEN** link "Đọc chi tiết" và link hủy nhận trỏ tới host công khai, mở được từ máy bất kỳ của người nhận

#### Scenario: Còn để giá trị mặc định localhost
- **WHEN** `DASHBOARD_BASE_URL`/`PUBLIC_API_BASE_URL` vẫn là `localhost` khi gửi ra ngoài
- **THEN** coi như cấu hình chưa sẵn sàng triển khai — email vẫn gửi được nhưng link chết và khả năng bị xếp Spam tăng mạnh
