## MODIFIED Requirements

### Requirement: Badge System Cleanup
Toàn bộ badge (Urgency, Impact, Role, Tier, Momentum) phải theo design system mới, có glassmorphism style nhẹ và labels rõ ràng.

#### Scenario: Badge labels không mơ hồ
- **WHEN** UrgencyBadge hoặc ImpactBadge render level "Trung bình"
- **THEN** phải hiển thị prefix: "Cấp thiết: Trung bình" hoặc "Ảnh hưởng: Trung bình" — không dùng "Trung bình" standalone

#### Scenario: Badge glassmorphism style
- **WHEN** bất kỳ badge render
- **THEN** phải có: `backdrop-filter: blur(8px)`, semi-transparent background, subtle border, border-radius 8px (không 999px tròn hoàn toàn)

### Requirement: Tooltip Clarity
Tất cả tooltip phải viết tiếng Việt dễ hiểu, không dùng thuật ngữ kỹ thuật.

#### Scenario: KPI tooltip giải thích ý nghĩa
- **WHEN** user hover icon info trên KPI "Tổng bản tin"
- **THEN** tooltip hiển thị: "Tổng số bài viết AI đã phân tích trong 7 ngày gần nhất. Bao gồm tất cả nguồn tin đang hoạt động."

#### Scenario: Score tooltips không dùng thuật ngữ kỹ thuật
- **WHEN** user hover actionability score
- **THEN** tooltip KHÔNG hiển thị "actionability_score >= 70%" — phải viết: "Đánh giá khả năng áp dụng: Điểm càng cao = bài viết có thể hành động ngay (thử nghiệm, áp dụng tool, thay đổi quy trình...)"

### Requirement: Skeleton Loading Upgrade
Loading state phải có shimmer animation premium.

#### Scenario: Shimmer skeleton khi loading
- **WHEN** data đang fetch
- **THEN** hiển thị skeleton cards với shimmer animation (gradient wave effect), featured skeleton card lớn hơn standard skeleton cards
