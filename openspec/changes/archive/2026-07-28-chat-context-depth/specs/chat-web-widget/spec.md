## ADDED Requirements

### Requirement: Working set insight hiển thị và sửa được

Widget SHALL duy trì một **working set** các insight đang được đưa vào ngữ cảnh hội thoại, và SHALL gửi
danh sách này kèm mỗi câu hỏi, **tách biệt** với văn bản câu hỏi.

Insight SHALL được thêm vào working set khi người dùng mở trang chi tiết của nó, và khi người dùng bấm vào
một trích dẫn trong câu trả lời. Widget SHALL hiển thị working set dưới dạng danh sách nhãn đọc được, mỗi
mục SHALL bỏ được bằng một thao tác. Khi working set vượt số ô sâu của service, widget SHALL giữ các mục
mới nhất.

Khi working set không rỗng, widget SHALL KHÔNG gửi kèm định danh bài đang xem theo cơ chế cũ — bài đang
xem đã nằm trong working set, gửi cả hai sẽ khiến service đi đường per-insight thay vì đường working set.

Actor: người dùng dashboard. Tiền điều kiện: widget đang mở.

#### Scenario: Đọc hai bài rồi so sánh
- **WHEN** người dùng mở insight A, mở tiếp insight B, rồi hỏi "so sánh hai cái này"
- **THEN** cả A và B đều nằm trong working set gửi lên, và câu trả lời đối chiếu đúng hai bài đó

#### Scenario: Bấm trích dẫn đưa bài vào ngữ cảnh
- **WHEN** người dùng bấm một trích dẫn `[n]` trong câu trả lời
- **THEN** insight tương ứng được thêm vào working set và các câu hỏi tiếp theo có thể nhắc tới nó

#### Scenario: Bỏ một mục khỏi working set
- **WHEN** người dùng bỏ một mục trong working set rồi hỏi tiếp
- **THEN** câu hỏi được gửi đi không còn tham chiếu tới insight đó

#### Scenario: Working set thay cho định danh bài đang xem
- **WHEN** người dùng đang ở trang chi tiết một insight và working set không rỗng
- **THEN** câu hỏi gửi lên mang working set và KHÔNG mang định danh bài đang xem theo cơ chế cũ

## MODIFIED Requirements

### Requirement: Cô lập hội thoại theo ngữ cảnh

Widget SHALL giữ **một luồng hội thoại** cho cả phiên. `history` gửi kèm mỗi câu hỏi SHALL là các lượt của
luồng đó.

Bất biến chống lẫn ngữ cảnh SHALL được bảo đảm bằng **ngữ cảnh đầy đủ** thay vì bằng sự cô lập: mọi insight
được nhắc tới trong `history` SHALL còn mặt trong ngữ cảnh của lượt hiện tại — hoặc trong working set, hoặc
trong phần index toàn hệ thống mà service dựng. Widget SHALL KHÔNG đưa phần câu trả lời đang stream (chưa
chốt) vào `history` của lượt sau.

**Lý do đảo bất biến cũ:** cô lập theo scope chặn được context drift, nhưng chính việc tách đôi làm hai bài
người dùng đã đọc riêng không bao giờ nằm chung một luồng — câu "so sánh hai bài vừa rồi" trở nên không thể
trả lời (đo 28/07/2026: recall@5 = 0/4). Drift cũ là một **mâu thuẫn** giữa `history` và ngữ cảnh; khi cả
hai bài đều nằm trong ngữ cảnh thì mâu thuẫn đó không còn tồn tại để phải chặn.

#### Scenario: Đổi bài rồi hỏi câu nối tiếp mập mờ
- **WHEN** người dùng xem bài A, hỏi một câu, chuyển sang bài B, rồi hỏi "rủi ro của nó thì sao?"
- **THEN** cả A và B đều có mặt trong ngữ cảnh gửi lên, và câu trả lời chỉ rõ đang nói về bài nào

#### Scenario: Rời trang chi tiết không xoá ngữ cảnh
- **WHEN** người dùng đã hỏi về một bài rồi rời trang chi tiết về danh sách
- **THEN** bài đó vẫn nằm trong working set và câu hỏi tiếp theo vẫn tham chiếu được tới nó

#### Scenario: Câu trả lời chưa chốt không lọt vào lịch sử
- **WHEN** một câu trả lời đang stream thì người dùng gửi câu hỏi mới sau khi nó chốt
- **THEN** lịch sử chỉ chứa nội dung đã chốt, không chứa phần dở dang

## REMOVED Requirements

### Requirement: Context chip theo insight đang mở

**Lý do:** chip một-lựa-chọn (gắn `insight_id` của bài đang mở, bỏ chip để về toàn cục) diễn tả được đúng
hai trạng thái — "một bài" hoặc "toàn hệ thống". Ca phải chữa là **hai bài cùng lúc**, mà chip không có
chỗ để biểu diễn.

**Thay bằng:** Requirement *Working set insight hiển thị và sửa được* — một TẬP tin sửa được, tự động nhận
bài khi mở trang chi tiết (giữ nguyên hành vi tiện lợi của chip) và nhận thêm bài khi bấm trích dẫn.

### Requirement: Chỉ báo phạm vi và chuyển scope hai chiều

**Lý do:** badge hai chiều là phiên bản tốt hơn của chip nhưng vẫn cùng giới hạn — nó mô tả một **chế độ**
(bài đang xem ↔ toàn hệ thống), trong khi ngữ cảnh nay là một **tập** tin. "Phạm vi" không còn là thứ để
bật/tắt.

**Thay bằng:** hàng chip working set. Nhãn `mode="expanded"` trên câu trả lời SHALL vẫn được giữ (xem
Requirement *Render câu trả lời theo luồng với trạng thái tiến trình*) vì đường per-insight cũ vẫn còn.
