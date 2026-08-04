## ADDED Requirements

### Requirement: Kết quả một kỳ phân biệt được nguyên nhân bỏ qua

Kết quả trả về và log của một kỳ bản tin SHALL phân biệt hai nguyên nhân bỏ qua người nhận: **bị chốt
chặn chu kỳ** (đã nhận trong `DELIVERY_MIN_GAP_HOURS` gần nhất — đúng thiết kế) và **không có tin nào
để gửi** (không insight nào khớp vai trò, hoặc mọi tin khớp đều đã gửi rồi). Hệ thống SHALL KHÔNG gộp
hai nguyên nhân này vào cùng một con số.

#### Scenario: Bỏ qua vì chốt chặn chu kỳ
- **WHEN** một người nhận đã nhận bản tin trong `DELIVERY_MIN_GAP_HOURS` gần nhất và kỳ mới chạy
- **THEN** kết quả kỳ đó đếm người này vào nhóm "bỏ qua vì chu kỳ", tách khỏi nhóm "không có tin"

#### Scenario: Bỏ qua vì không có tin khớp
- **WHEN** một người nhận active nhưng không insight nào trong lookback khớp vai trò của họ
- **THEN** kết quả kỳ đó đếm người này vào nhóm "không có tin", tách khỏi nhóm "bỏ qua vì chu kỳ"
- **AND** log nêu vai trò của người đó, để phân biệt "vai trò chưa có dữ liệu" với "pipeline đói tin"

#### Scenario: Đọc kết quả một kỳ
- **WHEN** vận hành viên đọc log sau một kỳ mà không ai nhận email
- **THEN** log cho biết đây là do chốt chặn chu kỳ hay do không có tin, không cần tra thêm nguồn khác

### Requirement: Tham số trần nhận giá trị không

Hàm chọn tin SHALL phân biệt "không truyền tham số trần" với "truyền trần bằng 0". Giá trị `0` SHALL
được tôn trọng đúng nghĩa (không lấy tin nào) chứ SHALL KHÔNG bị thay bằng giá trị mặc định.

#### Scenario: Trần bằng 0
- **WHEN** gọi hàm chọn tin với trần mỗi vai trò bằng `0`
- **THEN** không tin nào được chọn cho vai trò đó

#### Scenario: Không truyền trần
- **WHEN** gọi hàm chọn tin mà không truyền trần
- **THEN** hệ thống dùng `DELIVERY_MAX_ITEMS_PER_ROLE` / `DELIVERY_MAX_ITEMS_PER_EMAIL` từ cấu hình
