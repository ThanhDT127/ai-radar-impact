## ADDED Requirements

### Requirement: Bản tin định kỳ nhóm theo vai trò
Hệ thống SHALL gửi bản tin vào **Thứ Hai và Thứ Năm** lúc `DELIVERY_DIGEST_HOUR` (mặc định 08:00 giờ
VN), dùng cron có `timezone=Asia/Ho_Chi_Minh`. Hệ thống SHALL KHÔNG dùng `IntervalTrigger(days=3)`
(mốc bị tính lại sau mỗi lần restart nên nhịp trôi dạt) và SHALL KHÔNG dùng cron theo ngày-trong-tháng
`day='*/3'` (nhảy sai ở ranh giới tháng).

Cửa sổ lookback SHALL là `DELIVERY_DIGEST_LOOKBACK_HOURS` (mặc định **108 giờ**) — rộng hơn khoảng
cách hai kỳ (3–4 ngày) một cách cố ý, để job chạy trễ vài giờ không làm mất tin; phần chồng lấn do
`delivery_log` chặn.

#### Scenario: Kỳ bản tin Thứ Hai
- **WHEN** đến 08:00 giờ VN Thứ Hai và có insight khớp vai trò của người nhận trong lookback
- **THEN** người đó nhận đúng một email cho kỳ đó

#### Scenario: Kỳ không có tin nào khớp vai trò
- **WHEN** đến kỳ gửi mà không insight nào trong lookback khớp vai trò của người nhận
- **THEN** người đó không nhận email nào (không gửi email rỗng)

### Requirement: Chọn tin bằng xếp hạng, không bằng ngưỡng
Hệ thống SHALL xếp hạng mọi insight khớp vai trò trong lookback rồi lấy **top-N cứng**, thay vì lọc
theo một ngưỡng cố định.

Lý do: đo trên dữ liệu thật trong cửa sổ 108 giờ, vai trò `Security` có **26** insight đạt
`recommendations[role].urgency = "high"` trong khi `Data Scientist` có **0** (dù có 29 tin khớp vai
trò). Lọc theo ngưỡng vừa làm ngập người này vừa bỏ đói người kia; chỉ xếp hạng mới cho cả hai một
lượng tin ổn định.

Điểm xếp hạng, tính riêng cho từng vai trò `R`, SHALL theo thứ tự ưu tiên:
1. `recommendations[R].urgency` — `high` > `medium` > `low`; thiếu khoá hoặc giá trị ngoài tập đóng coi như `medium`
2. `impact_label` — `Nghiêm trọng` > `Cao` > `Trung bình` > `Thấp`
3. có ít nhất một `practical_indicators` cụ thể (`has_security_patch`, `has_api_change`, `has_migration_guide`)
4. `actionability_score` giảm dần
5. `intelligence_tier = "Strategic"` được cộng điểm
6. `trust_score` giảm dần
7. `published_at` mới hơn

Trần số lượng SHALL là `DELIVERY_MAX_ITEMS_PER_ROLE` (mặc định **2**) tin mỗi vai trò và
`DELIVERY_MAX_ITEMS_PER_EMAIL` (mặc định **3**) tin mỗi email — trần email áp lên tổng, không phải
cộng dồn theo số vai trò đăng ký.

Người nhận có ít nhất 1 insight khớp vai trò trong lookback SHALL nhận email, **kể cả khi không tin
nào đạt `urgency = "high"`**.

Insight khớp nhiều vai trò của **cùng một người** SHALL chỉ xuất hiện một lần, ở vai trò có điểm cao
hơn.

Phần dư SHALL được thể hiện bằng một dòng "+N tin khác" kèm link dashboard, KHÔNG liệt kê tiêu đề.

**Thứ tự hiển thị** SHALL đi từ khẩn cấp nhất xuống thấp nhất theo đúng điểm xếp hạng của vai trò
chứa tin đó:
- trong mỗi section vai trò, tin sắp giảm dần theo điểm (tiêu chí đầu tiên là `recommendations[R].urgency`)
- các section vai trò sắp theo tin đứng đầu của mình, nên vai trò có tin khẩn cấp nhất nằm trên cùng
- tin đầu tiên của email SHALL là tin có mức khẩn cấp cao nhất toàn email, và cũng là tin dùng dựng subject

Người nhận SHALL đọc được tin quan trọng nhất mà không phải cuộn trang.

#### Scenario: Thứ tự từ khẩn cấp cao xuống thấp
- **WHEN** email gồm 3 tin: một tin `urgency = high` cho `Security`, một tin `high` cho `AI Engineer` có `impact_label` thấp hơn, và một tin `medium` cho `Security`
- **THEN** section `Security` nằm trên `AI Engineer`, và trong section `Security` tin `high` đứng trước tin `medium`

#### Scenario: Vai trò có quá nhiều tin ảnh hưởng cao
- **WHEN** vai trò `Security` của người nhận có 26 insight đạt `urgency = "high"` trong lookback
- **THEN** email chứa đúng 2 tin xếp hạng cao nhất cho `Security` và dòng "+N tin khác" kèm link dashboard

#### Scenario: Vai trò không có tin nào ảnh hưởng cao
- **WHEN** vai trò `Data Scientist` của người nhận có 29 insight khớp nhưng không tin nào `urgency = "high"`
- **THEN** người đó vẫn nhận 2 tin xếp hạng cao nhất trong 29 tin đó

#### Scenario: Đăng ký nhiều vai trò
- **WHEN** người nhận đăng ký `[Security, AI Engineer, Tech Lead]` và mỗi vai trò đều có tin
- **THEN** email chứa tối đa 3 tin trên tổng (không phải 2 tin × 3 vai trò)

#### Scenario: Tin khớp hai vai trò của cùng một người
- **WHEN** người nhận đăng ký `[AI Engineer, Tech Lead]` và một insight khớp cả hai, điểm cho `AI Engineer` cao hơn
- **THEN** tin đó xuất hiện đúng một lần, trong section `AI Engineer`

### Requirement: Mỗi tin gửi đi phải đủ chi tiết để đọc ngay trong email
Vì mỗi kỳ chỉ gửi tối đa 3 tin, mỗi tin SHALL được render đầy đủ như trang chi tiết trên dashboard,
không phải một dòng tiêu đề. Nội dung mỗi tin SHALL gồm, khi field có dữ liệu:

- tiêu đề đầy đủ (**KHÔNG cắt ngắn**)
- badge `impact_label`, `intelligence_tier`, `adoption_ring`, và các `practical_indicators` có giá trị
- `signal`, `so_what`, `why_it_matters`, `summary_medium`
- khuyến nghị của **đúng vai trò chứa tin đó**: `action_type` + `note`
- `risks` nếu có
- link "Đọc chi tiết" về `{DASHBOARD_BASE_URL}/insights/{id}`

Field thiếu dữ liệu SHALL được bỏ qua, KHÔNG render nhãn rỗng hay placeholder.

#### Scenario: Tin có đủ trường
- **WHEN** render một tin có `signal`, `so_what`, `why_it_matters`, `summary_medium`, `risks` và khuyến nghị cho vai trò của section
- **THEN** email hiển thị đủ các phần đó cùng badge và link đọc chi tiết

#### Scenario: Insight cũ thiếu trường v2
- **WHEN** insight không có `so_what` hoặc `risks`
- **THEN** phần đó được bỏ qua hoàn toàn, các phần còn lại vẫn render bình thường

#### Scenario: Tiêu đề dài
- **WHEN** tiêu đề hiển thị dài hơn 110 ký tự
- **THEN** tiêu đề vẫn hiển thị nguyên vẹn trong thân email (chỉ subject của email mới bị giới hạn độ dài)

## MODIFIED Requirements

### Requirement: Chọn người nhận theo role
Recipient của một **bản tin** SHALL là các subscriber `active` có ít nhất 1 role trùng với
`affected_roles` của insight; insight có `affected_roles` chứa "Toàn công ty" SHALL gửi cho mọi
subscriber active.

Vai trò quyết định **cả người nhận lẫn thứ hạng tin**: điểm xếp hạng của một insight được tính riêng
cho từng vai trò, nên cùng một tin có thể vào email của người này và bị loại khỏi email của người kia.

Vai trò nằm trong `affected_roles` nhưng vắng trong `recommendations` SHALL được coi như
`urgency = medium` khi xếp hạng — không bị loại.

Subscriber có `roles` rỗng hoặc `active = false` SHALL KHÔNG nhận gì.

#### Scenario: Khớp một phần role
- **WHEN** insight có `affected_roles = [Dev, Security]` và subscriber đăng ký `[Security]`
- **THEN** subscriber đó thuộc danh sách nhận, tin được xếp hạng theo điểm của vai trò `Security`

#### Scenario: Insight toàn công ty
- **WHEN** insight có `affected_roles` chứa "Toàn công ty"
- **THEN** mọi subscriber active đều thuộc danh sách nhận

#### Scenario: Vai trò thiếu trong recommendations
- **WHEN** insight có `affected_roles = [Dev, Security]` nhưng `recommendations` chỉ có khoá `Security`
- **THEN** với người đăng ký `Dev`, tin vẫn được xếp hạng nhưng ở mức `urgency = medium`

### Requirement: Chống gửi trùng bằng delivery log
Mỗi lần gửi SHALL ghi `delivery_log (insight_id, subscriber_id, kind)` với ràng buộc unique; insight
đã có log cho một `subscriber_id` với cùng `kind` SHALL không được gửi lại cho người đó, kể cả khi job
chạy lại hoặc service restart. Cột định danh `chat_id` (Telegram) SHALL được thay bằng
`subscriber_id UUID` tham chiếu `subscribers(id)`.

`delivery_log` SHALL chỉ ghi cho tin **thực sự được gửi**, KHÔNG ghi cho tin bị loại vì trần số lượng.
Đây là thay đổi so với luật digest cũ ("ghi log cả phần vượt cap"): khi trần chỉ còn 3 tin/email, ghi
log toàn bộ tin khớp sẽ chôn vĩnh viễn hàng chục tin chưa ai đọc. Tin bị loại vì trần SHALL còn quyền
cạnh tranh ở kỳ kế tiếp nếu vẫn nằm trong lookback.

Chỉ ghi log khi adapter báo gửi thành công — lần gửi lỗi SHALL được thử lại ở kỳ sau.

Vì luật trên, ràng buộc unique CHỈ chặn gửi lại **cùng một tin** — nó KHÔNG chặn được lần chạy thừa
trong cùng một kỳ, vì lần đó sẽ lấy lô tin xếp hạng kế tiếp (là tin khác) và gửi tiếp. Do đó hệ thống
SHALL có thêm **chốt chặn chu kỳ**: bỏ qua người nhận nếu họ đã nhận bản tin trong
`DELIVERY_MIN_GAP_HOURS` giờ gần đây (mặc định 48 — nhỏ hơn khoảng cách hai kỳ 3–4 ngày nên không
chặn nhầm kỳ hợp lệ). So sánh thời gian SHALL thực hiện trong SQL bằng `now()` của DB.

#### Scenario: Chạy lại trong cùng kỳ
- **WHEN** job bản tin chạy lần thứ hai trong cùng ngày và vẫn còn hàng chục tin khớp chưa gửi
- **THEN** không người nhận nào nhận email thứ hai, và `delivery_log` không phát sinh dòng mới

#### Scenario: Kỳ kế tiếp sau khi qua chốt chặn
- **WHEN** đã quá `DELIVERY_MIN_GAP_HOURS` kể từ lần gửi trước và vẫn còn tin chưa gửi
- **THEN** người nhận nhận lô tin xếp hạng kế tiếp

#### Scenario: Job chạy lại sau restart
- **WHEN** job bản tin chạy lại sau khi service restart và gặp insight đã gửi trước đó
- **THEN** không gửi lại; không có bản ghi `delivery_log` trùng

#### Scenario: Tin bị loại vì trần số lượng
- **WHEN** một insight khớp vai trò nhưng xếp hạng 5 trong khi trần là 3
- **THEN** insight đó không được ghi `delivery_log`, và ở kỳ kế tiếp nó vẫn được xếp hạng cùng các tin mới

#### Scenario: Người nhận đổi địa chỉ email
- **WHEN** một subscriber đổi `email` nhưng giữ nguyên bản ghi
- **THEN** lịch sử `delivery_log` của họ vẫn còn nguyên và các tin đã gửi không bị gửi lại

### Requirement: Format message không dùng AI
Message SHALL được render thuần từ template + fields có sẵn của insight; delivery SHALL KHÔNG gọi
Gemini. Mọi nội dung trong email SHALL đã tồn tại trong bảng `insights` tại thời điểm render.

Nút inline "Hỏi về tin này" SHALL bị loại bỏ — đó là khái niệm của transport chat, không có tương
đương trong email.

#### Scenario: Render một kỳ bản tin
- **WHEN** engine render bản tin cho một người nhận
- **THEN** không có lượt gọi Gemini nào phát sinh trong toàn bộ chu kỳ gửi

### Requirement: Nội dung gửi đi phải là tiếng Việt và khớp dashboard
Mọi text hiển thị trong tin gửi đi SHALL là tiếng Việt. Tiêu đề tin SHALL dùng cùng luật với
dashboard (`InsightCard.tsx::makeDisplayTitle`): nếu `insights.title` không chứa ký tự có dấu tiếng
Việt và `summary_short` tồn tại thì hiển thị `summary_short`, ngược lại hiển thị `title`.

Lý do: `insights.title` là tiêu đề gốc của bài (phần lớn nguồn tiếng Anh). Nếu delivery và dashboard
dùng luật khác nhau, cùng một tin sẽ mang hai tiêu đề khác nhau ở hai nơi.

Tên topic và tên vai trò là ngoại lệ: SHALL giữ nguyên giá trị taxonomy vì dashboard cũng hiển thị
nguyên giá trị đó.

**Subject của email** SHALL dựng từ tiêu đề của tin xếp hạng cao nhất kèm phần đếm phần còn lại
(ví dụ `AI Radar 21/07: Microsoft vá 570 lỗ hổng bảo mật +2 tin khác`), cắt ở ranh giới từ khi vượt
độ dài hiển thị của client email. Subject SHALL KHÔNG viết HOA toàn bộ và KHÔNG dùng dấu chấm than
lặp — để giảm khả năng bị xếp spam.

#### Scenario: Tiêu đề gốc tiếng Anh
- **WHEN** insight có `title = "Microsoft Patches a Record 570 Security Flaws"` và `summary_short` tiếng Việt
- **THEN** tin gửi đi hiển thị `summary_short`, KHÔNG hiển thị tiêu đề tiếng Anh

#### Scenario: Tiêu đề gốc đã là tiếng Việt
- **WHEN** insight có `title = "Việt Nam ra mắt nền tảng AI mới"`
- **THEN** tin gửi đi giữ nguyên `title`

#### Scenario: Subject phản ánh tin quan trọng nhất
- **WHEN** bản tin gồm 3 tin, tin xếp hạng cao nhất là một cảnh báo bảo mật
- **THEN** subject chứa tiêu đề tin đó kèm "+2 tin khác", không phải một tiêu đề chung chung

## REMOVED Requirements

### Requirement: Alert tức thời theo mức ảnh hưởng tới vai trò
**Reason**: Kênh mới là email. Gửi email mỗi 5 phút gần như chắc chắn bị Gmail xếp spam, kéo theo cả
bản tin định kỳ vào thùng rác; người nhận cũng sẽ tự filter. Trần alert/giờ và cơ chế gom tin tổng
hợp sinh ra để chữa triệu chứng của nhịp này nên bị gỡ cùng.

**Migration**: Tiêu chí chọn tin của alert (`recommendations[role].urgency = "high"`) được giữ nguyên
và trở thành **tiêu chí xếp hạng số 1** của bản tin định kỳ — tin ảnh hưởng cao vẫn luôn đứng đầu
email của đúng vai trò, chỉ chậm hơn tối đa một kỳ. Gỡ job `delivery_alert_cycle`, các hàm
`run_alert_cycle`/`render_alert`/`render_alert_summary`/`count_alerts_last_hour`, và các env
`DELIVERY_ALERT_INTERVAL_MINUTES`, `DELIVERY_ALERT_LOOKBACK_HOURS`, `DELIVERY_MAX_ALERTS_PER_HOUR`.

### Requirement: Digest hàng ngày gom phần còn lại theo từng người
**Reason**: Thay bằng bản tin Thứ Hai + Thứ Năm nhóm theo **vai trò**, chọn bằng xếp hạng và giới hạn
3 tin mỗi email — ngược hẳn với digest cũ (gửi mọi tin khớp vai trò, tối đa 15, mỗi tin một dòng).
Khi không còn alert thì khái niệm "phần còn lại" cũng không còn nghĩa.

**Migration**: Xem các requirement "Bản tin định kỳ nhóm theo vai trò", "Chọn tin bằng xếp hạng,
không bằng ngưỡng" và "Mỗi tin gửi đi phải đủ chi tiết để đọc ngay trong email". Env
`DELIVERY_DIGEST_HOUR` và `DELIVERY_DIGEST_LOOKBACK_HOURS` giữ nguyên tên; mặc định lookback đổi
48 → 108 giờ.
