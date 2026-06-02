## MODIFIED Requirements

### Requirement: Classification bằng Gemini Flash

Hệ thống MUST gọi Gemini Flash 2.0 API để classify raw document theo taxonomy mới đã mở rộng (12 topics, 11 event_types).

#### Scenario: Classify thành công
- **WHEN** gửi normalized content của 1 raw document lên Gemini Flash
- **THEN** nhận về structured JSON chứa: `topics` (list), `event_type` (1 giá trị), `nature` (1 giá trị), `confidence` (0.0-1.0)

#### Scenario: Confidence thấp
- **WHEN** Gemini trả về `confidence < 0.5`
- **THEN** insight được tạo với `status=needs_review`, không broadcast tự động

#### Scenario: API error hoặc timeout
- **WHEN** Gemini API trả về error hoặc timeout (>60s)
- **THEN** raw document giữ `status=pending`, ghi log error, retry được ở lần chạy tiếp

### Requirement: Prompt engineering

Prompt gửi cho Gemini MUST structured rõ ràng, bao gồm taxonomy reference mới.

#### Scenario: Prompt chứa taxonomy mới
- **WHEN** gửi request classify lên Gemini
- **THEN** prompt bao gồm: danh sách 12 topics mới, danh sách 11 event_types mới, danh sách nature, yêu cầu trả về JSON format, yêu cầu kèm confidence score

### Requirement: Trust và Impact scoring mở rộng

Impact scoring MUST cập nhật cho 11 event types mới, bao gồm Breaking Change và Benchmark.

#### Scenario: Impact score từ event type mới
- **WHEN** tạo insight với `event_type = "Breaking Change"`
- **THEN** `impact_label = "Nghiêm trọng"`

#### Scenario: Impact score cho Benchmark
- **WHEN** tạo insight với `event_type = "Benchmark/So sánh"`
- **THEN** `impact_label = "Trung bình"`

#### Scenario: Impact score cho Hướng dẫn
- **WHEN** tạo insight với `event_type = "Hướng dẫn/Best Practice"`
- **THEN** `impact_label = "Trung bình"`

#### Scenario: Impact score cho Nghiên cứu/Paper
- **WHEN** tạo insight với `event_type = "Nghiên cứu/Paper"`
- **THEN** `impact_label = "Thấp"`

## ADDED Requirements

### Requirement: Taxonomy topics mở rộng

`ALLOWED_TOPICS` MUST chứa 12 topics developer-centric thay thế 10 topics cũ.

#### Scenario: Topics mới
- **WHEN** `build_prompt` được gọi
- **THEN** prompt chứa 12 topics: "AI/ML Ứng dụng", "AI/ML Nghiên cứu", "DevTools & Frameworks", "Cloud & Infrastructure", "Data Engineering", "Security & Compliance", "Software Architecture", "Developer Experience", "Platform & API", "Market & Competition", "Legal & Regulation", "Team & Process"

### Requirement: Event types mở rộng

`ALLOWED_EVENT_TYPES` MUST chứa 11 event types thay thế 9 event types cũ (thêm 3 mới, rename 1).

#### Scenario: Event types mới
- **WHEN** `build_prompt` được gọi
- **THEN** prompt chứa 11 event types: "Phát hành mới", "Thay đổi chính sách", "Cập nhật quy định", "Cảnh báo bảo mật", "Ngừng hỗ trợ/Deprecation", "Tín hiệu xu hướng", "Thảo luận cộng đồng", "Nghiên cứu/Paper", "Sự cố vận hành", "Breaking Change", "Benchmark/So sánh", "Hướng dẫn/Best Practice"

#### Scenario: Rename Ngừng hỗ trợ
- **WHEN** event_type cũ là "Ngừng hỗ trợ"
- **THEN** event_type mới là "Ngừng hỗ trợ/Deprecation"

### Requirement: Gemini sinh thêm 3 output fields mới

Prompt MUST yêu cầu Gemini trả thêm 3 fields trong JSON output.

#### Scenario: Sinh `so_what`
- **WHEN** Gemini analyze raw_document
- **THEN** output JSON có field `so_what` — 1 câu (≤200 ký tự) trả lời "bài này thay đổi gì cho team?"
- **THEN** `so_what` PHẢI KHÁC `signal` và `summary_short`

#### Scenario: Sinh `adoption_ring`
- **WHEN** Gemini analyze raw_document
- **THEN** output JSON có field `adoption_ring` — 1 trong 4 giá trị: Adopt, Trial, Assess, Hold
- **THEN** Adopt: nên dùng ngay. Trial: thử nghiệm. Assess: đánh giá thêm. Hold: chưa nên dùng.

#### Scenario: Sinh `practical_indicators`
- **WHEN** Gemini analyze raw_document
- **THEN** output JSON có `practical_indicators` là object JSON: `{ has_code_example: bool, has_benchmark: bool, has_api_change: bool, has_migration_guide: bool, has_security_patch: bool }`

#### Scenario: Graceful degradation cho 3 fields mới
- **WHEN** Gemini trả JSON malformed cho `so_what`, `adoption_ring`, hoặc `practical_indicators`
- **THEN** field bị lỗi = NULL, insight vẫn được lưu
- **THEN** log warning

### Requirement: Validate adoption_ring post-parse

Backend MUST validate `adoption_ring` chỉ chấp nhận giá trị hợp lệ.

#### Scenario: adoption_ring hợp lệ
- **WHEN** Gemini trả `adoption_ring = "Trial"`
- **THEN** giữ nguyên giá trị

#### Scenario: adoption_ring không hợp lệ
- **WHEN** Gemini trả `adoption_ring = "Maybe"`
- **THEN** `adoption_ring = NULL`
- **THEN** log warning

### Requirement: Two-pass pipeline flow trong AnalyzerService

`AnalyzerService.analyze_document()` MUST chạy gate trước deep analysis khi `ENABLE_GATE=true`.

#### Scenario: Document pass gate rồi deep analyze
- **WHEN** `ENABLE_GATE=true` AND document pass gate
- **THEN** gate result lưu vào `gate_score` variable
- **THEN** deep analysis chạy với prompt hiện tại (có taxonomy mới)
- **THEN** insight tạo với `actionability_score` tính từ composite formula

#### Scenario: Document bị filter bởi gate
- **WHEN** `ENABLE_GATE=true` AND document fail gate (actionability_score < threshold)
- **THEN** raw_document gán `status = 'low_signal'`
- **THEN** KHÔNG tạo insight
- **THEN** `_increment_daily_count()` KHÔNG tăng (gate call không tính vào cap)
