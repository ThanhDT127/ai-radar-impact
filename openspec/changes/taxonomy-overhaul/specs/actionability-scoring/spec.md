## ADDED Requirements

### Requirement: Composite actionability score

Hệ thống MUST tính `actionability_score` cho mỗi insight dùng composite formula 5 yếu tố, lưu vào cột `actionability_score` (Float) trong bảng `insights`.

#### Scenario: Tính score cho insight mới
- **WHEN** insight được tạo sau deep analysis
- **THEN** `actionability_score` = 0.30 × gate_score + 0.15 × confidence + 0.20 × trust_score + 0.25 × event_weight + 0.10 × recency_factor
- **THEN** kết quả là float 0.0-1.0, round 2 decimals

#### Scenario: Event weight lookup
- **WHEN** tính `event_weight` cho event_type
- **THEN** Breaking Change → 1.0, Cảnh báo bảo mật → 1.0, Sự cố vận hành → 0.9, Phát hành mới → 0.8, Ngừng hỗ trợ → 0.8, Cập nhật quy định → 0.7, Thay đổi chính sách → 0.7, Hướng dẫn/Best Practice → 0.6, Benchmark/So sánh → 0.6, Tín hiệu xu hướng → 0.4, Nghiên cứu/Paper → 0.3, Thảo luận cộng đồng → 0.3

#### Scenario: Recency factor
- **WHEN** tính `recency_factor` cho bài có `published_at`
- **THEN** `recency_factor = max(0, 1 - age_days / 30)`
- **THEN** bài 1 ngày tuổi ≈ 0.97, bài 30 ngày tuổi = 0, bài > 30 ngày = 0

#### Scenario: Recency khi không có published_at
- **WHEN** `published_at` là NULL
- **THEN** `recency_factor = 0.5` (neutral default)

### Requirement: Event type weight mapping

Hệ thống MUST duy trì `EVENT_TYPE_WEIGHTS` dict mapping event_type → weight (0.0-1.0), dùng cho composite score.

#### Scenario: Weight cho event type không có trong mapping
- **WHEN** event_type không match bất kỳ key nào trong `EVENT_TYPE_WEIGHTS`
- **THEN** default weight = 0.3

### Requirement: Backfill actionability cho insight cũ

Khi deploy, insight cũ MUST được backfill `actionability_score` dùng formula với `gate_score = 0.5` (default neutral).

#### Scenario: Backfill score cho insight có đủ data
- **WHEN** migration backfill chạy trên insight cũ có confidence, trust_score, event_type, published_at
- **THEN** `actionability_score` được tính với `gate_score = 0.5`

#### Scenario: Backfill score cho insight thiếu data
- **WHEN** insight cũ không có event_type
- **THEN** `actionability_score = NULL` (không tính được)
