## MODIFIED Requirements

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
ghi `delivery_log` cho lần đó, để chu kỳ sau gửi lại. Adapter SHALL giải phóng kết nối SMTP của lần
đó — bao gồm cả khi gửi lỗi — chứ SHALL KHÔNG bỏ tham chiếu mà để socket treo.

`ChannelRegistry` SHALL cấp adapter **mới cho mỗi lượt gửi** thay vì dùng chung một instance cho cả
tiến trình. Hai lượt gửi chạy chồng nhau trong cùng tiến trình SHALL KHÔNG dùng chung kết nối SMTP, và
việc một lượt kết thúc SHALL KHÔNG đóng kết nối của lượt còn lại.

#### Scenario: Gửi thành công một bản tin
- **WHEN** engine gọi `adapter.send()` với địa chỉ hợp lệ và nội dung bản tin
- **THEN** một email tới đúng địa chỉ đó, có cả phần text và phần HTML, `From` là `EMAIL_FROM`, và `delivery_log` được ghi

#### Scenario: SMTP lỗi giữa chừng
- **WHEN** SMTP trả lỗi khi gửi cho một người nhận
- **THEN** không có `delivery_log` nào được ghi cho người đó, các người nhận còn lại vẫn được gửi, và chu kỳ sau tin đó được gửi lại
- **AND** kết nối SMTP hỏng được đóng, không để socket treo chờ GC

#### Scenario: Nhiều người nhận
- **WHEN** có 5 subscriber active đủ điều kiện nhận bản tin
- **THEN** hệ thống gửi 5 email riêng biệt, mỗi email chỉ chứa địa chỉ của một người ở `To:`, không dùng BCC

#### Scenario: Hai lượt gửi chồng nhau trong cùng tiến trình
- **WHEN** một lượt gửi theo lịch cron đang chạy và một lượt gửi chạy tay bắt đầu trước khi lượt kia kết thúc
- **THEN** mỗi lượt dùng adapter riêng với kết nối SMTP riêng
- **AND** lượt kết thúc trước SHALL KHÔNG làm hỏng kết nối của lượt còn lại
