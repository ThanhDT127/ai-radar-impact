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

### Requirement: `recommendations` mang mức ảnh hưởng theo từng vai trò

Mỗi entry trong `recommendations` MUST có thêm khoá `urgency` thuộc tập đóng
`high | medium | low` (`ALLOWED_ROLE_URGENCY`), thể hiện mức ảnh hưởng của tin **tới riêng vai trò
đó** — KHÔNG phải mức ảnh hưởng của tin nói chung (đã có ở `insights.urgency`). Prompt MUST hướng dẫn
Gemini chấm tiết kiệm: `high` chỉ dành cho tin mà người giữ vai trò đó cần đọc ngay trong ngày.

#### Scenario: Cùng một tin, mức khác nhau theo vai trò
- **WHEN** Gemini phân tích một lỗ hổng bảo mật trong thư viện hệ thống với `affected_roles = [Security, Dev]`
- **THEN** `recommendations["Security"].urgency` = `high` còn `recommendations["Dev"].urgency` có thể là `medium` hoặc `low`

#### Scenario: Tin không phải bảo mật vẫn có thể `high`
- **WHEN** Gemini phân tích một bản phát hành model lớn với `affected_roles` chứa `AI Engineer`
- **THEN** `recommendations["AI Engineer"].urgency` ĐƯỢC PHÉP là `high`, không phụ thuộc `event_type` hay `insights.urgency`

### Requirement: Validate `recommendations` post-parse

Sau khi parse Gemini output, backend MUST validate `recommendations` để loại bỏ keys hallucinate và
giá trị ngoài tập đóng, bao gồm cả khoá `urgency`.

#### Scenario: Drop role không trong affected_roles
- **WHEN** Gemini trả `recommendations` có key không thuộc `affected_roles`
- **THEN** backend remove key đó khỏi recommendations trước khi lưu
- **THEN** log warning về role bị drop

#### Scenario: Drop `action_type` không hợp lệ
- **WHEN** value của `recommendations[role]` có `action_type` không thuộc closed set
- **THEN** backend remove cả entry đó
- **THEN** log warning

#### Scenario: `urgency` không hợp lệ hoặc thiếu
- **WHEN** `recommendations[role]` có `urgency` không thuộc `high|medium|low`, hoặc không có khoá `urgency`
- **THEN** backend đặt `urgency = "medium"` cho entry đó và giữ nguyên phần còn lại của entry
- **THEN** log warning nêu rõ role và giá trị bị thay

### Requirement: ALLOWED_ROLES là bộ 9 chức danh

`ALLOWED_ROLES` trong `app/ai/prompts.py` MUST là đúng 9 giá trị chức danh: `Data Analyst`,
`Data Scientist`, `AI Engineer`, `Data Engineer`, `Security`, `Dev`, `Tech Lead`,
`Người dùng phổ thông`, `Toàn công ty`.

Bộ này MUST tách bạch với `Source.target_roles` (13 giá trị theo chức năng phòng ban — xem spec
`source-region-tagging`). `affected_roles` và keys của `recommendations` chỉ nhận giá trị từ
`ALLOWED_ROLES`.

#### Scenario: Prompt expose đúng 9 vai trò
- **WHEN** `build_prompt` được gọi
- **THEN** prompt chứa đúng 9 vai trò trong `VAI TRÒ CHO PHÉP`
- **THEN** Gemini trả `affected_roles` là tập con của 9 giá trị này

#### Scenario: Từ chối vai trò thuộc taxonomy target_roles
- **WHEN** Gemini trả `affected_roles` chứa `DevOps` hoặc `Engineering` (giá trị của `target_roles`, không thuộc `ALLOWED_ROLES`)
- **THEN** backend drop giá trị đó và log warning

#### Scenario: Frontend label đồng bộ
- **WHEN** thêm/đổi tên giá trị trong `ALLOWED_ROLES`
- **THEN** `ROLE_DISPLAY_LABEL` + `ROLE_CLASS` (`RoleBadge.tsx`) và `TOOLTIP.role` (`TooltipContent.ts`) phải cập nhật cùng lúc, nếu không badge render không có nhãn/màu

### Requirement: Tìm kiếm Insights theo từ khóa từ Database (search-insights-backend)

Endpoint GET `/api/v1/insights` MUST hỗ trợ tham số truy vấn `search` để cho phép tìm kiếm các bản tin khớp với từ khóa từ database.

#### Scenario: Tìm kiếm với từ khóa hợp lệ
- **WHEN** Gửi yêu cầu GET `/api/v1/insights?search=npm`
- **THEN** Backend MUST trả về danh sách các insights chứa từ khóa "npm" trong tiêu đề (`title`) hoặc nội dung (`summary_short`, `summary_medium`, `signal`, `so_what`).

#### Scenario: Tìm kiếm với từ khóa không tồn tại
- **WHEN** Gửi yêu cầu GET `/api/v1/insights?search=nonexistentkeyword123`
- **THEN** Backend SHALL trả về danh sách rỗng (`items: []`) với tổng số lượng bằng 0 (`total: 0`).

---

### Requirement: Nâng cấp chất lượng dịch và tóm tắt của AI qua Prompting nâng cao

Hệ thống phân tích AI (Module M4 - AI Analysis) MUST sử dụng prompt hệ thống đã nâng cấp, áp dụng Negative Constraints và Few-shot Prompting để loại bỏ văn phong dịch máy rập khuôn và tạo ra các bản tóm tắt tiếng Việt tự nhiên, chuyên nghiệp.

#### Scenario: Thực thi ràng buộc tiêu cực (Negative Constraints)
- **WHEN** mô hình Gemini tiến hành phân tích văn bản và sinh các trường nội dung tiếng Việt (`summary_short`, `signal`, `why_it_matters`, `so_what`, `recommendations`)
- **THEN** output của mô hình MUST không chứa bất kỳ cụm từ mở đầu sáo rỗng nào trong danh sách cấm (ví dụ: "Đối với các team...", "Điều này quan trọng vì...", "Bài viết này nói về...")
- **AND** câu văn SHALL đi thẳng trực tiếp vào nội dung kỹ thuật hoặc hành động cụ thể.

#### Scenario: Sử dụng thuật ngữ chuyên ngành tự nhiên
- **WHEN** AI dịch và phân tích các bài viết kỹ thuật chứa thuật ngữ công nghệ phổ biến
- **THEN** mô hình SHALL giữ nguyên các thuật ngữ tiếng Anh thông dụng (như pipeline, CI/CD, API, container, cloud, framework, benchmark, deployment, repository, production, database) thay vì dịch sang tiếng Việt gượng ép hoặc tối nghĩa.

#### Scenario: Bảo toàn định dạng JSON schema đầu ra
- **WHEN** mô hình Gemini trả về kết quả phân tích dưới dạng JSON string
- **THEN** kết quả trả về MUST tuân thủ chính xác 100% cấu trúc schema định sẵn (bao gồm các trường: title, summary_short, summary_medium, signal, why_it_matters, so_what, urgency, momentum, intelligence_tier, adoption_ring, affected_roles, recommendations...)
- **AND** hệ thống SHALL phân tích và lưu trữ thành công vào Database mà không gặp bất kỳ lỗi parse JSON hay ValidationError nào.

### Requirement: Daily analysis cap persist qua Database

Hệ thống SHALL giới hạn số tài liệu phân tích mỗi ngày (`max_daily_analysis`, mặc định 500) bằng bộ đếm **persist trong DB**, đúng xuyên nhiều tiến trình và sống sót qua restart. Bộ đếm SHALL tính **mọi** tài liệu đã gọi Gemini (đạt trạng thái terminal `analyzed`, `low_signal`, hoặc `failed`), không chỉ tài liệu tạo được insight.

#### Scenario: Cap không reset giữa các lần chạy

- **WHEN** một tiến trình `run_analysis`/scheduler mới khởi động trong cùng ngày
- **THEN** số đã dùng được đọc từ DB (`COUNT(*) WHERE analyzed_at::date = today`), KHÔNG reset về 0
- **AND** `daily_remaining = max_daily_analysis - daily_used` phản ánh đúng tổng đã xử lý trong ngày

#### Scenario: Đếm cả doc bị gate loại và failed

- **WHEN** một tài liệu bị gate loại (`low_signal`) hoặc `failed` (vẫn tốn ≥1 gate call)
- **THEN** `analyzed_at` được set và tài liệu đó được tính vào cap trong ngày

#### Scenario: Dừng khi chạm cap

- **WHEN** `daily_used >= max_daily_analysis`
- **THEN** bước analysis dừng, log cảnh báo, KHÔNG gọi Gemini thêm cho tới ngày hôm sau

#### Scenario: Reset theo ngày

- **WHEN** sang ngày mới (theo UTC)
- **THEN** `daily_used` tính lại từ 0 do đếm theo `analyzed_at::date = today`

### Requirement: Đầu ra gate ràng buộc bằng schema

Lần gọi Gemini cho **gate pre-screening** MUST khai báo `response_schema` cho API, không chỉ
`response_mime_type` (vốn chỉ gợi ý định dạng, không ép cấu trúc). Tập đóng `content_type` MUST được
biểu diễn thành enum trong schema, và schema MUST dựng từ chính hằng số `ALLOWED_CONTENT_TYPES` trong
`app/ai/prompts.py` — KHÔNG chép tay giá trị, để schema không trôi khỏi tập đóng.

Lần gọi **deep analysis** MUST KHÔNG dùng `response_schema`. Đã thử và đo (20/07/2026): ràng buộc
schema khiến model sinh trường văn bản tự do (`why_it_matters`) lặp vô nghĩa tới ~6500 ký tự cho tới
khi chạm `max_output_tokens` và bị cắt giữa chuỗi, làm 100% document qua gate lỗi parse.
`max_length` trong schema KHÔNG cứu được vì Vertex không thực thi ràng buộc đó. Tập đóng ở nhánh này
do lớp validate post-parse bảo đảm.

#### Scenario: Gate không trả được `content_type` ngoài tập đóng
- **WHEN** Gemini gate định gán `content_type = "tutorial"` (không thuộc `ALLOWED_CONTENT_TYPES`)
- **THEN** API từ chối giá trị đó do ràng buộc enum

#### Scenario: Thêm giá trị vào tập đóng
- **WHEN** một giá trị mới được thêm vào `ALLOWED_CONTENT_TYPES` trong `prompts.py`
- **THEN** schema gửi cho Gemini tự động chứa giá trị đó, không cần sửa thêm chỗ nào khác

#### Scenario: Deep analysis giữ đầu ra không ràng buộc schema
- **WHEN** `analyze` gọi Gemini
- **THEN** config KHÔNG chứa `response_schema`; tập đóng được bảo đảm bởi `_validate_recommendations` / `_validate_affected_roles` / `_validate_adoption_ring`

### Requirement: Fail-open phải để lại dấu vết

Khi gate lỗi và document được cho đi thẳng vào deep analysis (fail-open), hệ thống MUST ghi lại rằng
document đó **chưa được gate chấm** (`raw_documents.gate_skipped`). Thống kê tỉ lệ qua gate MUST loại
các document này ra, vì chúng không phải bằng chứng nội dung đạt chuẩn.

#### Scenario: Gate lỗi parse
- **WHEN** `gate_analyze` trả về lỗi parse JSON cho một document
- **THEN** document vẫn được deep analysis (giữ nguyên fail-open) **và** `gate_skipped = true`

#### Scenario: Thống kê không tính document bỏ qua gate
- **WHEN** tính tỉ lệ qua gate của một nguồn
- **THEN** các document có `gate_skipped = true` không được tính vào tử số lẫn mẫu số

### Requirement: Log đủ dài để chẩn đoán lỗi parse

Khi parse JSON thất bại, hệ thống MUST log phần raw response đủ dài để nhìn thấy vị trí gây lỗi, kèm
tổng độ dài response. Log dài chỉ áp dụng ở nhánh lỗi, không áp cho đường chạy bình thường.

#### Scenario: Lỗi ở vị trí xa đầu chuỗi
- **WHEN** JSON hỏng ở ký tự thứ 517 của response
- **THEN** log chứa đủ nội dung để thấy ký tự đó, không bị cắt trước vị trí lỗi

