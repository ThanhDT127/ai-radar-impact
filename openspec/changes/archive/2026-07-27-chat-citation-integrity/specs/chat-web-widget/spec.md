## MODIFIED Requirements

### Requirement: Render citation thành link
Câu trả lời của bot SHALL hiển thị citations dưới dạng link; bấm citation SHALL điều hướng đến chi tiết insight tương ứng trong dashboard.

Widget SHALL giải marker `[n]` trong câu trả lời bằng **số marker `n` do server cấp phát**, KHÔNG bằng vị trí của phần tử trong mảng `citations`. Danh sách nguồn hiển thị kèm câu trả lời SHALL đánh số **khớp với marker trong câu**, không tự đánh số lại. Marker không tìm được citation tương ứng SHALL hiển thị như text thường, KHÔNG bao giờ trỏ sang insight khác.

#### Scenario: Bấm citation
- **WHEN** bot trả lời kèm citation
- **THEN** citation hiển thị title insight dạng link, bấm vào mở chi tiết insight đó

#### Scenario: Marker không liền mạch từ 1
- **WHEN** câu trả lời chứa marker `[3]`, `[7]`, `[12]` và `citations` mang `n` tương ứng 3, 7, 12
- **THEN** bấm `[3]` mở đúng insight có `n = 3`, bấm `[7]` mở đúng insight có `n = 7`, bấm `[12]` mở đúng insight có `n = 12`

#### Scenario: Marker xuất hiện không theo thứ tự tăng dần
- **WHEN** câu trả lời nhắc `[5]` trước rồi mới tới `[2]`
- **THEN** mỗi marker vẫn mở đúng insight mang `n` bằng chính con số đó, không hoán đổi cho nhau

#### Scenario: Danh sách nguồn khớp marker trong câu
- **WHEN** câu trả lời trích dẫn các insight mang `n` là 3, 7, 12
- **THEN** danh sách nguồn dưới câu trả lời hiển thị `[3]`, `[7]`, `[12]` — cùng con số với marker trong câu

#### Scenario: Marker không có citation tương ứng
- **WHEN** answer còn sót một marker mà `citations` không có phần tử `n` khớp
- **THEN** marker đó hiển thị như text thường, không thành link, và không trỏ tới insight nào khác
