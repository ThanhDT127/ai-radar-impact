## ADDED Requirements

### Requirement: Classification bằng Gemini Flash

Hệ thống gọi Gemini Flash 2.0 API để classify raw document theo taxonomy đã định nghĩa (topic, event_type, nature).

#### Scenario: Classify thành công
- **WHEN** gửi normalized content của 1 raw document lên Gemini Flash
- **THEN** nhận về structured JSON chứa: `topics` (list), `event_type` (1 giá trị), `nature` (1 giá trị), `confidence` (0.0-1.0)

#### Scenario: Confidence thấp
- **WHEN** Gemini trả về `confidence < 0.5`
- **THEN** insight được tạo với `status=needs_review`, không broadcast tự động

#### Scenario: API error hoặc timeout
- **WHEN** Gemini API trả về error hoặc timeout (>60s)
- **THEN** raw document giữ `status=pending`, ghi log error, retry được ở lần chạy tiếp

### Requirement: Summarization

Gemini Flash sinh summary ngắn gọn từ nội dung raw document.

#### Scenario: Sinh summary thành công
- **WHEN** gửi content lên Gemini Flash với prompt summarize
- **THEN** nhận về `summary_short` (1-2 câu, max 200 ký tự) và `summary_medium` (1 đoạn, max 500 ký tự)

#### Scenario: Summary phải bám nguồn
- **WHEN** summary được sinh ra
- **THEN** summary chỉ chứa thông tin có trong nội dung gốc — không suy diễn, không thêm thông tin ngoài

### Requirement: Trust và Impact scoring cơ bản

Giai đoạn này dùng rule-based scoring, không cần LLM.

#### Scenario: Trust score từ source tier
- **WHEN** tạo insight từ source có `trust_tier=High`
- **THEN** insight nhận `trust_score=0.8`

#### Scenario: Impact score mặc định
- **WHEN** tạo insight mới
- **THEN** `impact_label` được gán dựa trên `event_type`: Security alert → High, New release → Medium, Trend signal → Low

### Requirement: Tạo Insight record

Kết quả analysis được lưu thành insight trong database.

#### Scenario: Insight tạo thành công
- **WHEN** classify + summarize hoàn tất với confidence >= 0.5
- **THEN** tạo record `insights` với: title, summary_short, summary_medium, topics, event_type, nature, trust_score, impact_label, source_url, raw_document_id, status=published

#### Scenario: Insight luôn trỏ về source
- **WHEN** insight được tạo
- **THEN** insight bắt buộc có `source_url` (link gốc) và `raw_document_id` (FK tới raw_documents) — không tồn tại insight không có nguồn

### Requirement: Prompt engineering

Prompt gửi cho Gemini phải structured rõ ràng, bao gồm taxonomy reference.

#### Scenario: Prompt chứa taxonomy
- **WHEN** gửi request classify lên Gemini
- **THEN** prompt bao gồm: danh sách topics hợp lệ, danh sách event_types hợp lệ, danh sách nature hợp lệ, yêu cầu trả về JSON format, yêu cầu kèm confidence score
