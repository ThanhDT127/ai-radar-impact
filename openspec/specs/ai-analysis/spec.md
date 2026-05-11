## Purpose

AI analysis layer phân tích raw documents bằng Gemini Flash để classify, summarize và sinh các trường actionable (signal, why_it_matters, recommendations, risks). Backend tính thêm các trường rule-based (momentum, urgency, vietnam_relevance, trust_score, impact_label) để insight có đủ ngữ cảnh ra quyết định cho team đa vai trò.
## Requirements
### Requirement: Classification bằng Gemini Flash

Hệ thống MUST gọi Gemini Flash 2.0 API để classify raw document theo taxonomy đã định nghĩa (topic, event_type, nature).

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

Gemini Flash MUST sinh summary ngắn gọn từ nội dung raw document.

#### Scenario: Sinh summary thành công
- **WHEN** gửi content lên Gemini Flash với prompt summarize
- **THEN** nhận về `summary_short` (1-2 câu, max 200 ký tự) và `summary_medium` (1 đoạn, max 500 ký tự)

#### Scenario: Summary phải bám nguồn
- **WHEN** summary được sinh ra
- **THEN** summary chỉ chứa thông tin có trong nội dung gốc — không suy diễn, không thêm thông tin ngoài

### Requirement: Trust và Impact scoring cơ bản

Giai đoạn này MUST dùng rule-based scoring, không cần LLM.

#### Scenario: Trust score từ source tier
- **WHEN** tạo insight từ source có `trust_tier=High`
- **THEN** insight nhận `trust_score=0.8`

#### Scenario: Impact score mặc định
- **WHEN** tạo insight mới
- **THEN** `impact_label` được gán dựa trên `event_type`: Security alert → High, New release → Medium, Trend signal → Low

### Requirement: Tạo Insight record

Kết quả analysis MUST được lưu thành insight trong database.

#### Scenario: Insight tạo thành công
- **WHEN** classify + summarize hoàn tất với confidence >= 0.5
- **THEN** tạo record `insights` với: title, summary_short, summary_medium, topics, event_type, nature, trust_score, impact_label, source_url, raw_document_id, status=published

#### Scenario: Insight luôn trỏ về source
- **WHEN** insight được tạo
- **THEN** insight bắt buộc có `source_url` (link gốc) và `raw_document_id` (FK tới raw_documents) — không tồn tại insight không có nguồn

### Requirement: Prompt engineering

Prompt gửi cho Gemini MUST structured rõ ràng, bao gồm taxonomy reference.

#### Scenario: Prompt chứa taxonomy
- **WHEN** gửi request classify lên Gemini
- **THEN** prompt bao gồm: danh sách topics hợp lệ, danh sách event_types hợp lệ, danh sách nature hợp lệ, yêu cầu trả về JSON format, yêu cầu kèm confidence score

### Requirement: Gemini sinh thêm 4 actionable fields

Prompt MUST yêu cầu Gemini trả về 4 trường mới trong JSON output, ngoài các trường hiện có.

#### Scenario: Sinh `signal` cho mỗi insight
- **WHEN** Gemini analyze raw_document
- **THEN** output JSON có field `signal` — 1 câu cô đọng cốt lõi tín hiệu, khác title (title là sự kiện, signal là implication)

#### Scenario: Sinh `why_it_matters`
- **WHEN** Gemini analyze raw_document
- **THEN** output JSON có field `why_it_matters` — 1-2 câu giải thích tại sao tin này quan trọng với team phần mềm Việt Nam, không lặp lại tóm tắt

#### Scenario: Sinh `recommendations` chỉ cho affected_roles
- **WHEN** Gemini analyze raw_document và xác định `affected_roles = ["Engineering", "Data/AI"]`
- **THEN** output JSON có `recommendations` là dict với keys ⊆ `affected_roles`
- **THEN** mỗi value là object `{ "action_type": <enum>, "note": <str> }`
- **THEN** `action_type` ∈ {`watch`, `read`, `test`, `PoC`, `roadmap`}

#### Scenario: Sinh `risks` (có thể rỗng)
- **WHEN** Gemini analyze raw_document
- **THEN** output JSON có field `risks` là list[str] — các rủi ro nếu adopt (license, security, privacy, vendor-lock, cost, maturity)
- **THEN** rỗng `[]` nếu không có rủi ro đáng kể

#### Scenario: Graceful degradation khi parse lỗi
- **WHEN** Gemini trả JSON malformed cho 4 fields mới
- **THEN** insight vẫn được lưu với 4 fields = NULL
- **THEN** log warning với raw_document_id và lỗi parse

### Requirement: Backend tính 3 rule-based fields

Sau khi insight được tạo, backend MUST tính 3 trường rule-based dựa vào data có sẵn.

#### Scenario: Tính `momentum` từ semantic cluster
- **WHEN** insight được tạo và đã trải qua semantic dedup
- **THEN** nếu `cluster_size = 1` AND `cluster_age_days < 3` → `momentum = "new"`
- **THEN** nếu `cluster_size >= 3` AND `cluster_age_days < 7` → `momentum = "rising"`
- **THEN** trường hợp còn lại → `momentum = "mature"`

#### Scenario: Tính `urgency` từ impact + recency
- **WHEN** tạo insight với `impact_label` và `published_at`
- **THEN** `impact_label = "Nghiêm trọng"` AND age < 14 days → `urgency = "critical"`
- **THEN** `impact_label = "Cao"` AND age < 14 days → `urgency = "high"`
- **THEN** `impact_label = "Trung bình"` OR (`Cao` nhưng > 14 days) → `urgency = "medium"`
- **THEN** còn lại → `urgency = "low"`

#### Scenario: Tính `vietnam_relevance` từ source + topics
- **WHEN** tạo insight có `source.config.language` và `topics`
- **THEN** `language = "vi"` OR `topics` chứa `"Pháp lý/Tuân thủ"` → `vietnam_relevance = "high"`
- **THEN** `topics` chứa Vietnamese-specific topic → `medium`
- **THEN** còn lại → `low`

### Requirement: Validate `recommendations` post-parse

Sau khi parse Gemini output, backend MUST validate `recommendations` để loại bỏ keys hallucinate.

#### Scenario: Drop role không trong affected_roles
- **WHEN** Gemini trả `recommendations` có key không thuộc `affected_roles`
- **THEN** backend remove key đó khỏi recommendations trước khi lưu
- **THEN** log warning về role bị drop

#### Scenario: Drop `action_type` không hợp lệ
- **WHEN** value của `recommendations[role]` có `action_type` không thuộc closed set
- **THEN** backend remove cả entry đó
- **THEN** log warning

### Requirement: ALLOWED_ROLES mở rộng thêm 5 vai trò technical

`ALLOWED_ROLES` trong `app/ai/prompts.py` MUST chứa thêm 5 vai trò: `DevOps`, `Infrastructure`, `Security`, `BA/QA`, `Designer/UX` (tổng 13 roles).

#### Scenario: Prompt expose 5 role mới
- **WHEN** `build_prompt` được gọi
- **THEN** prompt chứa danh sách 13 vai trò trong `VAI TRÒ CHO PHÉP`
- **THEN** Gemini có thể trả `affected_roles` chứa giá trị mới (ví dụ `["DevOps", "Security"]`)

#### Scenario: Recommendations hợp lệ với role mới
- **WHEN** Gemini trả `recommendations = {"DevOps": {"action_type": "test", "note": "..."}}`
- **THEN** `_validate_recommendations` giữ nguyên entry vì `DevOps` ∈ `affected_roles`
- **THEN** insight lưu recommendation cho DevOps

#### Scenario: Backwards compatible với insight cũ
- **WHEN** insight cũ có `affected_roles = ["Engineering"]` (8 role taxonomy cũ)
- **THEN** không bị invalidate; vẫn render bình thường

