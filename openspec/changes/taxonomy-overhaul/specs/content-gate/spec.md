## ADDED Requirements

### Requirement: Gate prompt pre-screening

Hệ thống MUST chạy một gate prompt nhẹ trên mỗi raw document trước khi chạy deep analysis. Gate prompt trả về JSON đánh giá mức độ thiết thực của bài viết.

#### Scenario: Gate call thành công — bài pass gate
- **WHEN** raw document được gửi vào gate prompt với title và content (trích 2000 ký tự đầu)
- **THEN** Gemini trả JSON chứa: `actionability_score` (0.0-1.0), `content_type` (practical|strategic|theoretical|noise), `gate_reason` (string ≤ 100 ký tự), `pass_gate` (bool)
- **THEN** nếu `actionability_score >= 0.4` thì `pass_gate = true`

#### Scenario: Gate call thành công — bài bị filter
- **WHEN** gate prompt trả `actionability_score < 0.4`
- **THEN** `pass_gate = false`
- **THEN** raw document được gán `status = 'low_signal'`
- **THEN** hệ thống KHÔNG gọi deep analysis cho document này

#### Scenario: Gate call lỗi hoặc timeout
- **WHEN** gate Gemini API trả error hoặc timeout (> 30s)
- **THEN** hệ thống fallback: coi như `pass_gate = true` (để không mất bài do lỗi tạm)
- **THEN** log warning với raw_document_id và error message

### Requirement: Gate prompt sử dụng Gemini Flash với config nhẹ

Gate prompt MUST dùng Gemini Flash 2.0 với `max_output_tokens=200` và `temperature=0.0` để tối ưu cost và deterministic.

#### Scenario: Config gate call
- **WHEN** hệ thống gọi Gemini cho gate
- **THEN** `max_output_tokens = 200`
- **THEN** `temperature = 0.0`
- **THEN** `response_mime_type = "application/json"`

### Requirement: Gate threshold configurable

Gate threshold MUST configurable qua settings, mặc định 0.4.

#### Scenario: Sử dụng threshold từ settings
- **WHEN** hệ thống đánh giá `pass_gate`
- **THEN** so sánh `actionability_score` với `settings.gate_threshold` (default 0.4)

#### Scenario: Admin override threshold
- **WHEN** `GATE_THRESHOLD=0.3` được set trong env
- **THEN** bài có `actionability_score >= 0.3` sẽ pass gate

### Requirement: Feature flag bật/tắt gate

Hệ thống MUST hỗ trợ feature flag `ENABLE_GATE` (default `true`). Khi tắt, pipeline quay lại single-pass.

#### Scenario: Gate enabled (default)
- **WHEN** `ENABLE_GATE=true` hoặc không set
- **THEN** mọi document chạy gate trước deep analysis

#### Scenario: Gate disabled
- **WHEN** `ENABLE_GATE=false`
- **THEN** mọi document đi thẳng vào deep analysis (như pipeline cũ)
