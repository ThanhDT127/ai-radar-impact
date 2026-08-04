## ADDED Requirements

### Requirement: Nguồn web hiển thị phân biệt được với nguồn hệ thống

Widget SHALL hiển thị citation trỏ tới nguồn web khác biệt rõ với citation trỏ tới tin trong
hệ thống, tối thiểu bằng tên miền và một liên kết mở ra ngoài.

Lý do: tin trong hệ thống đã qua phân tích và chấm điểm tin cậy; nguồn web thì chưa. Trộn hai
loại vào cùng một kiểu hiển thị là để người dùng gán nhầm mức tin cậy.

Widget SHALL giải marker `[n]` bằng cách **tra theo trường `n`** trong danh sách citation, áp
dụng cho cả hai loại nguồn — KHÔNG dùng vị trí trong mảng.

#### Scenario: Câu trả lời trích cả hai loại nguồn
- **WHEN** câu trả lời chứa marker trỏ tới cả tin hệ thống và nguồn web
- **THEN** mỗi marker giải đúng nguồn của nó, và hai loại hiển thị phân biệt được

#### Scenario: Marker không liền mạch
- **WHEN** các marker trong câu trả lời không bắt đầu từ 1 hoặc bị ngắt quãng
- **THEN** mọi marker vẫn giải đúng nguồn theo `n`

### Requirement: Khối Search Suggestions

Khi câu trả lời có dùng tra cứu ngoài, widget SHALL hiển thị khối Search Suggestions do nhà
cung cấp trả về, kèm câu trả lời.

#### Scenario: Có tra cứu
- **WHEN** phản hồi mang dữ liệu Search Suggestions
- **THEN** widget hiển thị khối đó

#### Scenario: Không tra cứu
- **WHEN** phản hồi không mang dữ liệu Search Suggestions
- **THEN** widget không hiển thị khối nào và bố cục không đổi
