## ADDED Requirements

### Requirement: Tooltip hiển thị khi hover

#### Scenario: User hover vào badge trên desktop
- **WHEN** user di chuột vào bất kỳ badge nào (tier, urgency, impact, role, momentum, topic, event type, score)
- **THEN** sau 200ms xuất hiện popup tooltip chứa nội dung giải thích bằng tiếng Việt

#### Scenario: Tooltip tự ẩn khi rời chuột
- **WHEN** user di chuột ra khỏi badge
- **THEN** tooltip fade out trong 150ms

#### Scenario: Tooltip không hiện trên mobile
- **WHEN** thiết bị không hỗ trợ hover (touch-only)
- **THEN** tooltip không được render (dùng `@media (hover: hover)`)

---

### Requirement: Nội dung tooltip chính xác theo loại

#### Scenario: Tier badge tooltip
- **WHEN** user hover vào badge "Strategic"
- **THEN** tooltip hiện: "Bài mang tính chiến lược — xu hướng dài hạn, cần theo dõi nhưng không cần hành động ngay"

#### Scenario: Tier badge tooltip - Tactical
- **WHEN** user hover vào badge "Tactical"
- **THEN** tooltip hiện: "Bài có thể hành động ngay — tool mới, bản vá bảo mật, breaking change cần xử lý"

#### Scenario: Urgency badge tooltip
- **WHEN** user hover vào badge urgency "Khẩn cấp"
- **THEN** tooltip hiện: "Mức cấp thiết cao nhất — cần xem xét và phản hồi trong vòng 24 giờ"

#### Scenario: Actionability score tooltip
- **WHEN** user hover vào chỉ số "⚡ 73%"
- **THEN** tooltip hiện: "Điểm hành động (0-100%): Đánh giá mức độ có thể áp dụng ngay. Dựa trên: độ tin cậy nguồn, loại sự kiện, độ mới, và chất lượng phân tích AI"

#### Scenario: Trust score tooltip
- **WHEN** user hover vào chỉ số "🛡️ Uy tín 80%"
- **THEN** tooltip hiện: "Độ tin cậy nguồn (0-100%): Vendor chính thức > Tech press > Blog chuyên môn > Cộng đồng"

---

### Requirement: Tooltip positioning và overflow

#### Scenario: Tooltip không bị cắt bởi container
- **WHEN** badge nằm ở cạnh phải màn hình
- **THEN** tooltip tự điều chỉnh position sang trái để không bị overflow

#### Scenario: Chỉ 1 tooltip tại 1 thời điểm
- **WHEN** user hover nhanh qua nhiều badges liên tiếp
- **THEN** chỉ tooltip cuối cùng được hiển thị, các tooltip trước bị hủy

---

### Requirement: Accessible cho screen readers

#### Scenario: Screen reader đọc tooltip content
- **WHEN** badge có tooltip được focus bằng keyboard
- **THEN** tooltip content được liên kết qua `aria-describedby` để screen reader đọc được
