## ADDED Requirements

### Requirement: Chỉ báo phạm vi và chuyển scope hai chiều

Khi người dùng đang ở trang chi tiết một insight, widget SHALL hiển thị **chỉ báo phạm vi (scope)** hiện
tại — "Bài đang xem" hoặc "Toàn hệ thống" — và SHALL cho phép chuyển đổi **hai chiều** giữa hai phạm vi đó
bằng một thao tác, **không cần điều hướng trang**. Đây là cơ chế chuyển scope tường minh, thay cho việc bỏ
context chip một chiều.

Chuyển phạm vi SHALL đổi luồng hội thoại tương ứng theo cơ chế cô lập scope (mỗi scope một luồng riêng);
widget SHALL KHÔNG mang lượt của scope này sang scope kia.

Câu trả lời được service mở rộng tự động (`mode="expanded"`) SHALL được đánh dấu để người dùng biết nó dựa
trên tìm kiếm **toàn hệ thống**, không chỉ bài đang xem.

#### Scenario: Hiển thị scope hiện tại
- **WHEN** người dùng mở widget khi đang ở trang chi tiết một insight
- **THEN** widget hiển thị chỉ báo phạm vi cho biết đang hỏi trong phạm vi "Bài đang xem"

#### Scenario: Chuyển scope hai chiều
- **WHEN** người dùng bấm chuyển sang "Toàn hệ thống" rồi bấm chuyển lại "Bài đang xem"
- **THEN** mỗi lần bấm đổi phạm vi ngay tại chỗ, không rời trang, và câu hỏi tiếp theo chạy đúng phạm vi đang hiển thị

#### Scenario: Chuyển scope đổi luồng hội thoại
- **WHEN** người dùng chuyển từ "Bài đang xem" sang "Toàn hệ thống"
- **THEN** widget hiển thị luồng hội thoại của scope toàn cục, không hiển thị lượt hỏi về bài; `history` gửi kèm không chứa lượt của scope bài

#### Scenario: Đánh dấu câu trả lời mở rộng
- **WHEN** service trả về câu trả lời với `mode="expanded"`
- **THEN** widget đánh dấu bong bóng trả lời đó là kết quả tìm trên toàn hệ thống, phân biệt với trả lời trong phạm vi bài
