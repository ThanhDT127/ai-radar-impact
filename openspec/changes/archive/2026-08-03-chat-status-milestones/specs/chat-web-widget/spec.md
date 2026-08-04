## MODIFIED Requirements

### Requirement: Render câu trả lời theo luồng với trạng thái tiến trình

Widget SHALL tiêu thụ endpoint streaming và render câu trả lời **tăng dần** khi token đến.
Khi nhận sự kiện chốt, widget SHALL gắn danh sách citation vào câu trả lời; nếu sự kiện chốt là
fail‑closed, widget SHALL **thay** phần text đã stream bằng nội dung không‑đủ‑căn‑cứ. Widget
SHALL vô hiệu hoá nút gửi trong khi một câu trả lời đang stream.

Trong lúc chờ, widget SHALL hiển thị các mốc tiến trình dưới dạng **danh sách tích luỹ**: mốc
đã qua giữ lại ở dạng mờ kèm dấu hoàn thành, mốc hiện tại hiển thị nổi bật.

Trước đây widget hiển thị **một dòng duy nhất bị ghi đè** mỗi khi có mốc mới, nên người dùng
không thấy được chuỗi việc đã diễn ra.

Widget SHALL phân biệt mốc bằng trường `key` của sự kiện, KHÔNG bằng cách so sánh chuỗi hiển
thị — chuỗi mang số liệu nên hai lần phát cùng một mốc luôn khác nhau.

Widget SHALL hiển thị tối đa **4** dòng; vượt quá thì bỏ dòng cũ nhất.

Widget SHALL KHÔNG hiển thị thanh tiến trình dạng phần trăm hay ước lượng thời gian còn lại.

#### Scenario: Nhiều mốc khác nhau đến trong một lượt
- **WHEN** luồng SSE phát nhiều sự kiện `status` với `key` khác nhau
- **THEN** mỗi mốc hiện thành một dòng riêng, các dòng trước vẫn thấy được ở dạng mờ

#### Scenario: Cùng một mốc được phát lại
- **WHEN** hai sự kiện `status` có cùng `key`
- **THEN** dòng tương ứng được cập nhật tại chỗ, không sinh dòng trùng

#### Scenario: Vượt trần số dòng
- **WHEN** số mốc trong một lượt vượt quá 4
- **THEN** widget hiện 4 mốc gần nhất và bỏ dòng cũ nhất

#### Scenario: Câu trả lời được chốt
- **WHEN** sự kiện `commit` tới
- **THEN** toàn bộ khối tiến trình biến mất, chỉ còn câu trả lời cuối

#### Scenario: Chưa có mốc nào
- **WHEN** người dùng vừa bấm Gửi và chưa có sự kiện `status` nào
- **THEN** widget hiển thị dòng chờ mặc định

#### Scenario: Server cũ không gửi `key`
- **WHEN** sự kiện `status` không mang `key`
- **THEN** widget vẫn hiển thị `text` và không báo lỗi

#### Scenario: `key` không nằm trong tập widget biết
- **WHEN** sự kiện `status` mang một `key` widget chưa biết
- **THEN** widget vẫn hiện nó như một dòng mới, KHÔNG bỏ qua
