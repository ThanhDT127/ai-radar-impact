## ADDED Requirements

### Requirement: Sự kiện tiến trình mang định danh mốc ổn định

Mỗi sự kiện `status` trên luồng SSE SHALL mang một trường `key` thuộc **tập đóng** các mốc
pipeline, tách bạch khỏi chuỗi hiển thị `text`.

Tập đóng SHALL được khai báo tại **một chỗ duy nhất** và dùng chung giữa backend và frontend.
Sửa câu chữ tiếng Việt của `text` SHALL KHÔNG làm đổi hành vi render của client.

Đường blocking (`POST /api/v1/chat`, không có `emit`) SHALL không đổi hành vi: không sự kiện
nào được phát, payload trả về giữ nguyên.

#### Scenario: Hai mốc khác nhau trong cùng một lượt
- **WHEN** pipeline đi qua hai mốc khác nhau
- **THEN** hai sự kiện `status` được phát với hai giá trị `key` khác nhau

#### Scenario: Cùng một mốc phát lại với số liệu mới
- **WHEN** cùng một mốc được phát lại trong một lượt
- **THEN** sự kiện mang cùng `key` và client cập nhật tại chỗ thay vì thêm dòng mới

#### Scenario: Đường blocking
- **WHEN** client gọi `POST /api/v1/chat`
- **THEN** không sự kiện `status` nào được phát và câu trả lời giống hệt trước change này

### Requirement: Status phát từ mốc thật và mang số liệu của lượt

Service SHALL phát status tại các mốc **thực sự xảy ra** trong pipeline, và mỗi mốc SHALL mang
dữ liệu chỉ đúng cho lượt đó khi dữ liệu đó tồn tại.

Service SHALL KHÔNG phát status theo bộ đếm thời gian, SHALL KHÔNG xoay vòng các cách diễn đạt
đồng nghĩa cho cùng một mốc, và SHALL KHÔNG phát tiến trình dạng phần trăm.

Ngoài các mốc đã có, service SHALL phát thêm:

- **`ranked`** — sau khi xếp hạng xong, mang số tin khớp và tổng số tin được xét.
- **`pinned`** — khi tập tin ghim từ lịch sử hội thoại khác rỗng, mang tiêu đề tin ghim.
- **`retrying`** — trước khi thực hiện lượt hỏi lại do câu trả lời bị cắt.

#### Scenario: Câu hỏi toàn cục
- **WHEN** người dùng hỏi một câu tra cứu toàn cục
- **THEN** mốc `ranked` được phát sau khi xếp hạng xong, mang số tin khớp thật của lượt đó

#### Scenario: Chưa có số liệu thì chưa phát
- **WHEN** ứng viên đã nạp từ DB nhưng chưa xếp hạng
- **THEN** mốc `ranked` SHALL chưa được phát

#### Scenario: Lượt có tin ghim từ lịch sử
- **WHEN** lịch sử hội thoại làm ít nhất một tin được ghim vào ngữ cảnh lượt hiện tại
- **THEN** mốc `pinned` được phát kèm tiêu đề tin ghim

#### Scenario: Cơ chế ghim bị tắt
- **WHEN** `chat_history_pin_slots = 0` hoặc lịch sử rỗng
- **THEN** mốc `pinned` SHALL KHÔNG được phát

#### Scenario: Câu trả lời bị cắt và phải hỏi lại
- **WHEN** lượt gọi model kết thúc vì chạm trần token và service thực hiện lượt hỏi lại
- **THEN** mốc `retrying` được phát **trước** lượt hỏi lại

#### Scenario: Câu trả lời không bị cắt
- **WHEN** lượt gọi model kết thúc bình thường
- **THEN** mốc `retrying` SHALL KHÔNG được phát

### Requirement: Phát status không làm thay đổi nội dung câu trả lời

Việc phát status SHALL KHÔNG đụng tới xếp hạng, dựng ngữ cảnh, grounding, hay bất kỳ thành
phần nào quyết định nội dung câu trả lời. `build_context()` SHALL vẫn là **hàm thuần**: không
I/O, không phát sự kiện.

#### Scenario: Bộ đo xếp hạng không đổi
- **WHEN** chạy lại RS harness sau change này
- **THEN** kết quả trùng khít baseline trước change, không cần chốt lại
