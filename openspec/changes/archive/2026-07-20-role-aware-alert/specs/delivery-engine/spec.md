## MODIFIED Requirements

### Requirement: Alert tức thời cho insight critical
Hệ thống SHALL quét định kỳ (mặc định mỗi 5 phút) các insight mới và gửi alert cho những subscriber
mà **vai trò của chính họ** được đánh giá là chịu ảnh hưởng cao từ tin đó, tức
`recommendations[role].urgency = "high"`. Điều kiện cũ "insight có `urgency = critical`" KHÔNG còn
được dùng để chọn tin alert. Chỉ insight có `created_at` trong cửa sổ lookback cấu hình
(`DELIVERY_ALERT_LOOKBACK_HOURS`, mặc định 24 giờ) mới được xét.

Ngữ nghĩa alert là **"tin có ảnh hưởng lớn tới vai trò của bạn, đáng đọc ngay"** — KHÔNG phải "khẩn
cấp, phải xử lý ngay".

#### Scenario: Cùng một tin, chỉ vai trò bị ảnh hưởng cao nhận alert
- **WHEN** insight có `affected_roles = [Security, Dev]` với `recommendations["Security"].urgency = "high"` và `recommendations["Dev"].urgency = "medium"`
- **THEN** subscriber đăng ký `Security` nhận alert, subscriber chỉ đăng ký `Dev` KHÔNG nhận alert (tin đó rơi vào digest của họ)

#### Scenario: Tin không phải bảo mật vẫn alert được
- **WHEN** insight có `event_type = "Phát hành mới"` (nên `insights.urgency` không phải `critical`) nhưng `recommendations["AI Engineer"].urgency = "high"`
- **THEN** subscriber đăng ký `AI Engineer` nhận alert

#### Scenario: Insight cũ chưa có urgency theo vai trò
- **WHEN** insight được tạo trước change này nên `recommendations[role]` không có khoá `urgency`
- **THEN** coi như `medium` và KHÔNG gửi alert cho bất kỳ vai trò nào

#### Scenario: Insight critical cũ ngoài lookback
- **WHEN** hệ thống khởi động với các insight có `created_at` cũ hơn cửa sổ lookback
- **THEN** không alert nào được gửi cho các insight đó

#### Scenario: Bão alert
- **WHEN** số alert phát sinh trong 1 giờ vượt trần cấu hình
- **THEN** các alert vượt trần được gom thành 1 tin tổng hợp thay vì gửi lẻ từng tin

### Requirement: Chọn người nhận theo role
Recipient của một **digest** SHALL là các subscriber active có ít nhất 1 role trùng với
`affected_roles` của insight; insight có `affected_roles` chứa "Toàn công ty" SHALL gửi cho mọi
subscriber active.

Recipient của một **alert** SHALL hẹp hơn: ngoài điều kiện giao vai trò ở trên, vai trò đó còn MUST
có mặt trong `recommendations` với `urgency = "high"`. Vai trò nằm trong `affected_roles` nhưng vắng
trong `recommendations` KHÔNG đủ điều kiện nhận alert.

#### Scenario: Khớp một phần role (digest)
- **WHEN** insight có `affected_roles = [Dev, Security]` và subscriber đăng ký `[Security]`
- **THEN** subscriber đó thuộc danh sách nhận digest

#### Scenario: Insight toàn công ty
- **WHEN** insight có `affected_roles` chứa "Toàn công ty"
- **THEN** mọi subscriber active đều thuộc danh sách nhận digest

#### Scenario: Vai trò thiếu trong recommendations không nhận alert
- **WHEN** insight có `affected_roles = [Dev, Security]` nhưng `recommendations` chỉ có khoá `Security`
- **THEN** subscriber chỉ đăng ký `Dev` không nhận alert cho tin đó, dù có trong `affected_roles`

#### Scenario: Không gửi trùng alert và digest
- **WHEN** một insight đã được gửi alert cho subscriber X
- **THEN** insight đó KHÔNG xuất hiện trong digest của X (kể cả insight cũ từng alert theo luật `critical` trước 2026-07-20)

### Requirement: Nội dung gửi đi phải là tiếng Việt và khớp dashboard
Mọi text hiển thị trong tin Telegram SHALL là tiếng Việt. Tiêu đề tin SHALL dùng cùng luật với
dashboard (`InsightCard.tsx::makeDisplayTitle`): nếu `insights.title` không chứa ký tự có dấu tiếng
Việt và `summary_short` tồn tại thì hiển thị `summary_short`, ngược lại hiển thị `title`.

Lý do: `insights.title` là tiêu đề gốc của bài (phần lớn nguồn tiếng Anh). Nếu delivery và dashboard
dùng luật khác nhau, cùng một tin sẽ mang hai tiêu đề khác nhau ở hai nơi.

#### Scenario: Tiêu đề gốc tiếng Anh
- **WHEN** insight có `title = "Microsoft Patches a Record 570 Security Flaws"` và `summary_short` tiếng Việt
- **THEN** tin Telegram hiển thị `summary_short`, KHÔNG hiển thị tiêu đề tiếng Anh

#### Scenario: Tiêu đề gốc đã là tiếng Việt
- **WHEN** insight có `title = "Việt Nam ra mắt nền tảng AI mới"`
- **THEN** tin Telegram giữ nguyên `title`

#### Scenario: Dòng digest quá dài
- **WHEN** tiêu đề hiển thị dài hơn 110 ký tự (thường do dùng `summary_short`)
- **THEN** dòng trong digest được cắt ở ranh giới từ kèm dấu `…`; tin alert KHÔNG bị cắt

#### Scenario: Từ ngữ khớp ngữ nghĩa alert mới
- **WHEN** render tin alert hoặc tin gom khi vượt trần
- **THEN** dùng từ "tin đáng đọc ngay" thay cho "cảnh báo", và biểu tượng 🔴 (mức `high`) thay cho 🚨
