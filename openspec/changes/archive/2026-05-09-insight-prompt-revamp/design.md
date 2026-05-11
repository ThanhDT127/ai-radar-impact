## Context

Hệ thống hiện tại sinh insight với 2 trường nội dung chính: `summary_short` (tóm tắt 1-2 câu) và `summary_medium` (đoạn 4-6 câu). Cả hai đều trả lời câu hỏi *"Có chuyện gì xảy ra?"* nhưng không trả lời *"Tại sao tôi nên quan tâm?"* và *"Tôi nên làm gì?"*.

User feedback rõ: với team đa vai trò ở Rạng Đông, radar chưa thúc đẩy hành động vì insight thiếu lớp khuyến nghị cụ thể theo role và thiếu ngữ cảnh tại sao tin này quan trọng với team phần mềm Việt Nam.

### Modules bị ảnh hưởng

- **M4 (AI Analysis)**: Refactor prompt + JSON schema + parser; logic rule-based mới
- **M5 (Storage)**: Migration thêm 7 cột vào `insights`
- **M6 (API)**: Schemas + routes trả thêm 7 fields
- **M7 (Frontend)**: Card + Detail UI thêm sections mới

### Trạng thái hiện tại

- `prompts.py:87` truncate content tới 6000 chars (gotham — đã biết)
- Insight model có: title, summary_short, summary_medium, topics, event_type, nature, trust_score, impact_label, confidence, affected_roles, source_url, ai_raw_response, cluster_id, is_primary
- Confidence < 0.3 → discard (không tạo insight)
- AnalyzerService map trust_tier → trust_score và event_type → impact_label sau khi parse AI output

## Goals / Non-Goals

**Goals:**
- 4 fields AI-generated (`signal`, `why_it_matters`, `recommendations`, `risks`) thực sự actionable, không lặp lại tóm tắt
- 3 fields rule-based (`momentum`, `urgency`, `vietnam_relevance`) deterministic, không phụ thuộc AI
- Backwards compatible: insights cũ không có 7 fields vẫn render đúng (null-safe)
- Graceful degradation: nếu Gemini trả JSON malformed cho fields mới, insight vẫn được tạo với fields = null
- Frontend phân tách rõ "insight cũ" (chỉ summary) vs "insight mới" (có signal/recommendations) trong UI

**Non-Goals:**
- Không thay đổi taxonomy/closed sets
- Không thay đổi threshold/mappings hiện có
- Không backfill bắt buộc — script regenerate là optional helper
- Không thêm push delivery (Teams/email)

## Decisions

### D1: Schema lai (4 AI + 3 rule), không full-AI

Toàn bộ 7 fields qua AI có 3 rủi ro: (1) JSON malformed do prompt phình to, (2) latency tăng, (3) hallucinate dimensions có thể derive deterministically. Chia ra:

- **AI generates**: `signal`, `why_it_matters`, `recommendations`, `risks` — yêu cầu hiểu ngữ cảnh
- **Rule derives**: `momentum`, `urgency`, `vietnam_relevance` — có thể tính từ data có sẵn

### D2: `momentum` từ semantic cluster

```python
def compute_momentum(insight, cluster_size, cluster_age_days):
    if cluster_size <= 1:
        return "new" if cluster_age_days < 3 else "mature"
    if cluster_size >= 3 and cluster_age_days < 7:
        return "rising"
    return "mature"
```

Yêu cầu `dedup_engine` expose cluster_size + earliest_published_at.

### D3: `urgency` rule

```
critical: impact_label = "Nghiêm trọng" AND age < 14 days
high:     impact_label = "Cao" AND age < 14 days
medium:   impact_label IN (Trung bình, Cao but >14d)
low:      Theo dõi, Thấp, hoặc impact_label NULL
```

### D4: `vietnam_relevance` rule

```
high:   source.config.language = "vi" OR topics CONTAINS "Pháp lý/Tuân thủ"
medium: topics CONTAINS bất kỳ Vietnamese-specific topic nào
low:    còn lại
```

(Có thể tinh chỉnh sau nếu thấy quá lạc quan)

### D5: `recommendations` chỉ cho roles trong `affected_roles`

Nếu insight có affected_roles = ["Engineering", "Data/AI"], chỉ generate khuyến nghị cho 2 role này, không hallucinate cho 6 role còn lại. Prompt yêu cầu Gemini chỉ trả keys ⊆ affected_roles.

### D6: `action_type` closed set

```
watch    — chỉ theo dõi, chưa cần làm gì
read     — đáng đọc kỹ để hiểu sâu
test     — thử nghiệm cá nhân/local
PoC      — đề xuất proof-of-concept với team
roadmap  — đưa vào roadmap chính thức
```

5 levels này rõ ràng, không trùng lặp. Tránh `ignore` (đã = không có rec) và `alert` (đã có urgency).

### D7: JSON schema cho AI output

Mở rộng prompt yêu cầu trả thêm 4 fields:

```json
{
  "title": "...",
  "summary_short": "...",
  "summary_medium": "...",
  "topics": [...],
  "event_type": "...",
  "nature": "...",
  "affected_roles": [...],
  "confidence": 0.85,
  "signal": "Mô hình mã nguồn mở mới đạt hiệu năng GPT-4 ở chi phí 1/10",
  "why_it_matters": "Team có thể giảm phụ thuộc OpenAI; chi phí hạ tầng AI nội bộ giảm đáng kể.",
  "recommendations": {
    "Engineering": {
      "action_type": "test",
      "note": "Thử qua HF Inference API trước khi tự host"
    },
    "Data/AI": {
      "action_type": "PoC",
      "note": "Benchmark trên use case nội bộ Q1/2026"
    }
  },
  "risks": ["License hạn chế thương mại", "Maturity thấp ở tiếng Việt"]
}
```

### D8: Frontend handling missing fields

Insight cũ không có 7 fields mới → frontend render fallback: hiển thị `summary_short` thay `signal`, hide các sections không có data thay vì render "N/A".

### D9: Backfill là optional

Tạo `backend/app/scripts/regenerate_insights.py` chấp nhận `--limit N`, `--since DATE`, `--source-id UUID` — chạy thủ công khi muốn upgrade insights cũ. Không phải part của migration tự động.

### API endpoints bị ảnh hưởng

- `GET /api/v1/insights` — response thêm 7 fields
- `GET /api/v1/insights/{id}` — response thêm 7 fields + `references` đã có
- `GET /api/v1/insights/stats` — không đổi

### Bảng DB bị ảnh hưởng

`insights` table:

```sql
ALTER TABLE insights
  ADD COLUMN signal TEXT,
  ADD COLUMN why_it_matters TEXT,
  ADD COLUMN recommendations JSONB,
  ADD COLUMN risks TEXT[],
  ADD COLUMN momentum VARCHAR(20),
  ADD COLUMN urgency VARCHAR(20),
  ADD COLUMN vietnam_relevance VARCHAR(20);
```

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| Gemini trả JSON malformed do prompt phức tạp hơn | Try/except parse từng field; fields mới null nếu parse lỗi; insight vẫn lưu với fields cũ |
| Latency tăng do prompt + output dài hơn | Đo trước/sau; nếu > 30% slower, cân nhắc tách AI call thành 2 lượt |
| Hallucinate khuyến nghị cho roles ngoài affected_roles | Prompt nhấn mạnh; validator post-parse drop keys không hợp lệ |
| Rule cho urgency/momentum/vietnam_relevance quá lạc quan/bi quan | Theo dõi distribution sau 1 tuần; tinh chỉnh thresholds |
| User confusion vì insights cũ không có fields mới | UI hide gracefully; có thể chạy regenerate script khi cần |
| Cluster size chưa expose từ dedup_engine | Task riêng — sửa `dedup_engine.py` thêm method `get_cluster_metadata(cluster_id)` |
