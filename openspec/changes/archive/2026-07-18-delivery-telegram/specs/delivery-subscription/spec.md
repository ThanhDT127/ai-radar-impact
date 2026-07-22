# delivery-subscription

## ADDED Requirements

### Requirement: Đăng ký nhận tin theo role qua bot
Người dùng SHALL đăng ký nhận tin bằng lệnh `/subscribe`: bot hiển thị inline keyboard đa chọn các role từ `ALLOWED_ROLES` (9 job-title roles trong `app/ai/prompts.py`); lựa chọn được lưu vào bảng `subscribers` theo `chat_id`. Chạy `/subscribe` lại SHALL cho phép sửa danh sách role hiện có.

#### Scenario: Đăng ký lần đầu
- **WHEN** người dùng gửi `/subscribe` và chọn "AI Engineer" + "Dev" rồi xác nhận
- **THEN** bảng `subscribers` có bản ghi (chat_id, roles=[AI Engineer, Dev], active=true) và bot xác nhận các role đã đăng ký

#### Scenario: Sửa role đã đăng ký
- **WHEN** subscriber hiện có gửi `/subscribe` và đổi lựa chọn role
- **THEN** bản ghi được cập nhật theo lựa chọn mới, không tạo bản ghi trùng

### Requirement: Hủy và xem trạng thái đăng ký
`/unsubscribe` SHALL ngừng mọi tin gửi tới chat đó (đặt `active=false`, giữ bản ghi); `/status` SHALL hiển thị các role đang đăng ký và trạng thái nhận tin.

#### Scenario: Hủy đăng ký
- **WHEN** subscriber gửi `/unsubscribe`
- **THEN** bot xác nhận, và chat đó không nhận alert/digest nào nữa cho đến khi `/subscribe` lại

#### Scenario: Xem trạng thái
- **WHEN** subscriber gửi `/status`
- **THEN** bot liệt kê role đã đăng ký và cho biết đang nhận tin hay đã tắt

### Requirement: Định danh bằng chat_id, không cần tài khoản hệ thống
Subscription SHALL dùng Telegram `chat_id` làm định danh duy nhất; không yêu cầu liên kết với tài khoản/auth của dashboard. Lệnh `/start` SHALL upsert bản ghi `subscribers` (roles rỗng, active) nếu chưa có — bản ghi này là dấu vết "chat đã `/start`" cho các consumer khác (vd. chatbot Q&A).

#### Scenario: Người dùng mới chưa từng dùng dashboard
- **WHEN** một người chỉ có Telegram (chưa từng đăng nhập dashboard) thực hiện `/start` và `/subscribe`
- **THEN** người đó nhận tin bình thường theo role đã chọn
