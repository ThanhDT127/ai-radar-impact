## Why

Insights hiện tại chỉ tóm tắt nội dung sự kiện (`summary_short`, `summary_medium`) nhưng không trả lời câu hỏi user thực sự cần: "Tại sao tin này quan trọng với team mình?" và "Cần làm gì với thông tin này?". Team đa vai trò (Dev, AI/ML, DA/DE, DevOps, Bảo mật, PM/BA, Content, Leadership) nhưng radar không phân hoá khuyến nghị theo vai trò.

Kết quả: dashboard có thông tin nhưng team không biết hành động → radar chưa tạo giá trị thực tế. Đây là root cause được user xác định, ưu tiên cao hơn việc mở rộng nguồn.

## What Changes

Thêm 7 trường mới vào insight, chia làm 2 nhóm:

**4 trường AI sinh ra (Gemini)**:
- `signal`: 1 câu cô đọng cốt lõi tín hiệu (khác với title vì là *implication*, không phải tin)
- `why_it_matters`: 1-2 câu giải thích tại sao tin này quan trọng với team phần mềm VN
- `recommendations`: dict `role → { action_type, note }` — chỉ generate cho roles trong `affected_roles`
  - `action_type` ∈ {`watch`, `read`, `test`, `PoC`, `roadmap`}
- `risks`: list ngắn gọn các rủi ro nếu adopt (license, security, privacy, vendor-lock, cost, maturity); rỗng nếu không có

**3 trường rule-based (backend tính)**:
- `momentum`: `new` | `rising` | `mature` — derive từ semantic cluster size + age
- `urgency`: `critical` | `high` | `medium` | `low` — kết hợp impact_label + recency
- `vietnam_relevance`: `high` | `medium` | `low` — derive từ source language + topic match

## Capabilities

### Modified Capabilities
- `ai-analysis`: prompt sinh thêm 4 actionable fields; parser xử lý JSON mở rộng; rule logic cho 3 fields còn lại
- `insight-api`: GET endpoints trả thêm 7 fields (additive, backwards compatible)
- `insight-dashboard`: Card hiển thị `urgency` badge + `signal` (thay summary nếu có); Detail page hiển thị full `recommendations` theo role + `why_it_matters` + `risks`

## Impact

- **Backend code**: `ai/prompts.py`, `services/analyzer.py`, `models/insight.py`, `schemas/insight.py`, `routes/insights.py`, `services/dedup_engine.py` (cần expose cluster_size cho momentum)
- **Database**: 7 cột mới trong `insights` (Alembic migration); `signal`, `why_it_matters` là TEXT; `recommendations` JSONB; `risks` ARRAY[TEXT]; `momentum`, `urgency`, `vietnam_relevance` là VARCHAR
- **Frontend**: `InsightCard`, `InsightDetail`, components mới `UrgencyBadge`, `RecommendationsByRole`, `MomentumIndicator`
- **API**: Response schema additive (không break clients hiện tại)
- **Dependencies**: Không thêm
- **Phase**: Phase 2

## Non-goals

- Không thay đổi taxonomy roles/topics/event_types/natures hiện có
- Không thay đổi confidence threshold (vẫn 0.3)
- Không thay đổi rule-based mappings hiện có (trust_tier→trust_score, event_type→impact_label)
- Không thêm scheduler tự động regenerate insights
- Không thêm Teams/email digest (sẽ là change riêng sau)
- Backfill insights cũ là **optional**, không bắt buộc trong scope này
