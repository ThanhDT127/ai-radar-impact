# delivery-engine

## Purpose

Đẩy insight tới người dùng qua kênh ngoài (channel-neutral; transport telegram đã gỡ 21/07, đang làm lại bằng email) thay vì bắt họ mở dashboard: alert cho tin cần
biết ngay, digest gom tin còn lại theo ngày. Chọn người nhận theo vai trò đăng ký, chống gửi trùng
bằng `delivery_log`, và render message thuần template (không gọi AI).

## Requirements

### Requirement: Alert tức thời theo mức ảnh hưởng tới vai trò
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

### Requirement: Digest hàng ngày gom phần còn lại theo từng người
Hệ thống SHALL gửi 1 bản tin digest mỗi ngày vào giờ cấu hình (`DELIVERY_DIGEST_HOUR`, mặc định 08:00
giờ VN) cho từng subscriber, gồm các insight trong cửa sổ lookback
(`DELIVERY_DIGEST_LOOKBACK_HOURS`, mặc định 48 giờ) khớp role đã đăng ký, nhóm theo topic, tối đa 15
insight (phần dư ghi chú "+N tin khác" kèm link dashboard).

"Phần còn lại" SHALL được tính **theo từng subscriber**, không phải theo thuộc tính toàn cục của
insight: digest của một người gồm mọi tin khớp vai trò mà **chính người đó** không đủ điều kiện nhận
alert. Cùng một insight có thể là alert với người này và là tin digest với người kia. Cột
`insights.urgency` KHÔNG còn được dùng để phân hoạch alert/digest.

Mọi insight khớp trong kỳ digest SHALL được ghi `delivery_log`, kể cả phần vượt cap hiển thị — tin dư
không dồn sang digest hôm sau.

#### Scenario: Digest sáng
- **WHEN** đến giờ digest và có 8 insight mới khớp role của subscriber từ lần digest trước
- **THEN** subscriber nhận đúng 1 message digest chứa 8 insight nhóm theo topic

#### Scenario: Tin critical không có vai trò nào `high`
- **WHEN** insight có `insights.urgency = critical` nhưng không vai trò nào của subscriber được chấm `urgency = "high"`
- **THEN** tin đó thuộc digest của subscriber (trước đây bị loại vì là critical)

#### Scenario: Không có tin mới
- **WHEN** đến giờ digest mà không có insight mới khớp role của subscriber
- **THEN** subscriber đó không nhận message nào (không gửi digest rỗng)

#### Scenario: Quá 15 insight
- **WHEN** có 22 insight mới khớp role của subscriber
- **THEN** digest hiển thị 15 insight và dòng "+7 tin khác" kèm link dashboard; cả 22 insight được ghi delivery_log nên digest hôm sau không lặp lại 7 tin dư

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

### Requirement: Nội dung gửi đi phải là tiếng Việt và khớp dashboard
Mọi text hiển thị trong tin gửi đi SHALL là tiếng Việt. Tiêu đề tin SHALL dùng cùng luật với
dashboard (`InsightCard.tsx::makeDisplayTitle`): nếu `insights.title` không chứa ký tự có dấu tiếng
Việt và `summary_short` tồn tại thì hiển thị `summary_short`, ngược lại hiển thị `title`.

Lý do: `insights.title` là tiêu đề gốc của bài (phần lớn nguồn tiếng Anh). Nếu delivery và dashboard
dùng luật khác nhau, cùng một tin sẽ mang hai tiêu đề khác nhau ở hai nơi.

Tên topic là ngoại lệ: SHALL giữ nguyên giá trị taxonomy (`DevTools & Frameworks`…) vì dashboard cũng
hiển thị nguyên giá trị đó.

#### Scenario: Tiêu đề gốc tiếng Anh
- **WHEN** insight có `title = "Microsoft Patches a Record 570 Security Flaws"` và `summary_short` tiếng Việt
- **THEN** tin gửi đi hiển thị `summary_short`, KHÔNG hiển thị tiêu đề tiếng Anh

#### Scenario: Tiêu đề gốc đã là tiếng Việt
- **WHEN** insight có `title = "Việt Nam ra mắt nền tảng AI mới"`
- **THEN** tin gửi đi giữ nguyên `title`

#### Scenario: Dòng digest quá dài
- **WHEN** tiêu đề hiển thị dài hơn 110 ký tự (thường do dùng `summary_short`)
- **THEN** dòng trong digest được cắt ở ranh giới từ kèm dấu `…`; tin alert KHÔNG bị cắt

#### Scenario: Từ ngữ khớp ngữ nghĩa alert mới
- **WHEN** render tin alert hoặc tin gom khi vượt trần
- **THEN** dùng từ "tin đáng đọc ngay" thay cho "cảnh báo", và biểu tượng 🔴 (mức `high`) thay cho 🚨
