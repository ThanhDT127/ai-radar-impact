# delivery-engine

## ADDED Requirements

### Requirement: Alert tức thời cho insight critical
Hệ thống SHALL quét định kỳ (mặc định mỗi 5 phút) các insight mới có `urgency = critical` và gửi alert đến các subscriber có role giao với `affected_roles` của insight. Chỉ insight có `created_at` trong cửa sổ lookback cấu hình (`DELIVERY_ALERT_LOOKBACK_HOURS`, mặc định 24 giờ) mới được xét.

#### Scenario: Insight critical mới xuất hiện
- **WHEN** analyzer tạo insight mới với `urgency = critical` có `affected_roles` chứa "Security"
- **THEN** trong vòng 5 phút, mọi subscriber đã đăng ký role "Security" nhận được alert Telegram

#### Scenario: Insight critical cũ ngoài lookback
- **WHEN** hệ thống khởi động với các insight critical có `created_at` cũ hơn cửa sổ lookback
- **THEN** không alert nào được gửi cho các insight đó

#### Scenario: Bão alert
- **WHEN** số alert phát sinh trong 1 giờ vượt trần cấu hình
- **THEN** các alert vượt trần được gom thành 1 tin tổng hợp thay vì gửi lẻ từng tin

### Requirement: Digest hàng ngày cho tin không critical
Hệ thống SHALL gom các insight không critical trong cửa sổ lookback (`DELIVERY_DIGEST_LOOKBACK_HOURS`, mặc định 48 giờ) chưa gửi cho chat đó và gửi 1 bản tin digest mỗi ngày vào giờ cấu hình (`DELIVERY_DIGEST_HOUR`, mặc định 08:00 giờ VN) cho từng subscriber, chỉ gồm insight khớp role đã đăng ký, nhóm theo topic, tối đa 15 insight (phần dư ghi chú "+N tin khác" kèm link dashboard). Mọi insight khớp trong kỳ digest SHALL được ghi `delivery_log`, kể cả phần vượt cap hiển thị — tin dư không dồn sang digest hôm sau.

#### Scenario: Digest sáng
- **WHEN** đến giờ digest và có 8 insight mới khớp role của subscriber từ lần digest trước
- **THEN** subscriber nhận đúng 1 message digest chứa 8 insight nhóm theo topic

#### Scenario: Không có tin mới
- **WHEN** đến giờ digest mà không có insight mới khớp role của subscriber
- **THEN** subscriber đó không nhận message nào (không gửi digest rỗng)

#### Scenario: Quá 15 insight
- **WHEN** có 22 insight mới khớp role của subscriber
- **THEN** digest hiển thị 15 insight và dòng "+7 tin khác" kèm link dashboard; cả 22 insight được ghi delivery_log nên digest hôm sau không lặp lại 7 tin dư

### Requirement: Chọn người nhận theo role
Recipient của một insight SHALL là các subscriber active có ít nhất 1 role trùng với `affected_roles` của insight; insight có `affected_roles` chứa "Toàn công ty" SHALL gửi cho mọi subscriber active.

#### Scenario: Khớp một phần role
- **WHEN** insight có `affected_roles = [Dev, Security]` và subscriber đăng ký `[Security]`
- **THEN** subscriber đó thuộc danh sách nhận

#### Scenario: Insight toàn công ty
- **WHEN** insight có `affected_roles` chứa "Toàn công ty"
- **THEN** mọi subscriber active đều thuộc danh sách nhận

### Requirement: Chống gửi trùng bằng delivery log
Mỗi lần gửi SHALL ghi `delivery_log (insight_id, chat_id, kind)` với ràng buộc unique; insight đã có log cho một chat_id với cùng kind SHALL không được gửi lại cho chat đó, kể cả khi job chạy lại hoặc service restart.

#### Scenario: Job chạy lại sau restart
- **WHEN** alert job chạy lại sau khi service restart và gặp insight critical đã gửi trước đó
- **THEN** không gửi lại; không có bản ghi delivery_log trùng

### Requirement: Format message không dùng AI
Message SHALL được render thuần từ template + fields có sẵn của insight (title, signal, why_it_matters, urgency, link dashboard); delivery SHALL KHÔNG gọi Gemini. Alert SHALL kèm nút inline "Hỏi về tin này".

#### Scenario: Render alert
- **WHEN** engine render alert cho một insight
- **THEN** message chứa title, signal, why_it_matters, link về dashboard và nút inline "💬 Hỏi về tin này", không có lượt gọi Gemini nào phát sinh
