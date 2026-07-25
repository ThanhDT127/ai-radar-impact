## ADDED Requirements

### Requirement: Render câu trả lời theo luồng với trạng thái tiến trình

Widget SHALL tiêu thụ endpoint streaming và render câu trả lời **tăng dần** khi token đến, thay cho việc chờ
trọn câu rồi hiện một lần. Trong lúc chờ, widget SHALL hiển thị **trạng thái tiến trình** do server phát (ví
dụ đang tìm trong hệ thống, đang tìm toàn hệ thống) thay cho một spinner đơn.

Khi nhận sự kiện chốt, widget SHALL gắn danh sách citation vào câu trả lời; nếu sự kiện chốt là fail‑closed,
widget SHALL **thay** phần text đã stream bằng nội dung không‑đủ‑căn‑cứ, KHÔNG giữ lại text ungrounded. Widget
SHALL vô hiệu hoá nút gửi trong khi một câu trả lời đang stream để tránh gửi trùng.

Nếu người dùng đổi scope hoặc rời ngữ cảnh trong khi một câu trả lời đang stream, widget SHALL huỷ luồng đang
chạy và SHALL KHÔNG nhập phần text dở vào luồng hội thoại của scope mới.

#### Scenario: Câu trả lời chảy dần kèm trạng thái
- **WHEN** người dùng gửi câu hỏi và server đang xử lý
- **THEN** widget hiện trạng thái tiến trình rồi các phần câu trả lời xuất hiện dần, và citations gắn vào khi luồng chốt

#### Scenario: Fail‑closed hoán text
- **WHEN** sự kiện chốt báo câu trả lời không đủ căn cứ
- **THEN** widget thay phần đã stream bằng thông báo không‑đủ‑căn‑cứ, không để lại nội dung ungrounded

#### Scenario: Đổi scope khi đang stream
- **WHEN** người dùng đổi insight hoặc chuyển scope trong khi câu trả lời đang stream
- **THEN** widget huỷ luồng đang chạy và luồng hội thoại của scope mới không chứa phần text dở

#### Scenario: Chống gửi trùng khi đang stream
- **WHEN** một câu trả lời đang được stream
- **THEN** nút gửi bị vô hiệu hoá cho tới khi luồng kết thúc
