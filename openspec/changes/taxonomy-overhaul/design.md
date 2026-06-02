## Context

AI Radar hiện dùng single-pass pipeline: mọi raw document đều được gửi vào Gemini Flash với prompt nặng (~4096 tokens output). Taxonomy 10 topics quá generic ("Trí tuệ nhân tạo" gom cả paper lẫn phát hành SDK), 9 event types thiếu loại quan trọng cho dev (Breaking Change, Benchmark). Kết quả: dashboard surface nhiều bài noise, không phân biệt tin cần hành động ngay vs đọc cho biết.

### Modules bị ảnh hưởng
- **M4 (AI Analysis)** — trọng tâm: taxonomy, prompts, scoring, two-pass flow
- **M5 (Insight Repository)** — schema mới: 5 cột thêm
- **M6 (Dashboard)** — filter & render fields mới

### API endpoints bị ảnh hưởng
- `GET /api/v1/insights` — thêm query params: `intelligence_tier`, `sort_by=actionability_score`
- `GET /api/v1/insights/{id}` — response thêm 5 fields mới
- `GET /api/v1/stats/overview` — thêm tier distribution

### Bảng DB bị ảnh hưởng
- `insights` — thêm 5 cột: `actionability_score` (Float), `intelligence_tier` (String(20)), `so_what` (Text), `adoption_ring` (String(20)), `practical_indicators` (JSONB)

### Model AI
- Gemini Flash 2.0 (giữ nguyên)
- Gate prompt dùng chung model, giảm output tokens (200 vs 4096)

## Goals / Non-Goals

**Goals:**
- Giảm noise: filter ≥40% bài không thiết thực trước khi deep analyze
- Phân tầng nội dung: tactical (hành động ngay) / operational / strategic / informational
- Taxonomy developer-centric: 12 topics + 11 event types chính xác hơn
- Actionability ranking: composite score để sort insight theo mức độ cần hành động
- Tiết kiệm ~55% Gemini tokens nhờ gate loại bài noise sớm

**Non-Goals:**
- KHÔNG làm pgvector semantic dedup (Phase 3 — riêng change)
- KHÔNG thay đổi delivery logic (n8n, email — không liên quan)
- KHÔNG thêm model AI mới (giữ Gemini Flash 2.0)
- KHÔNG thêm role/RBAC mới (user roles giữ nguyên)
- KHÔNG refactor frontend framework (vẫn React + CSS Modules)

## Decisions

### D1: Two-Pass vs Single-Pass Pipeline

**Chọn: Two-Pass (Gate → Deep)**

Gate prompt nhẹ (~200 token output) chạy trước, trả 4 fields: `actionability_score` (0-1), `content_type` (practical/strategic/theoretical/noise), `gate_reason` (1 câu), `pass_gate` (bool).

Bài có `actionability_score < 0.4` → skip deep analysis → gán `status='low_signal'`.

**Alternatives considered:**
- Single-pass with stricter prompt: vẫn tốn full tokens cho noise — bỏ
- Client-side keyword filter: quá thô, miss context → bỏ
- Confidence threshold tăng (0.3 → 0.5): chỉ filter bài ambiguous, không filter bài rõ ràng nhưng không thiết thực

**Trade-off:** Thêm 1 API call per document, nhưng gate call rẻ hơn deep call 20x. Net saving ~55%.

### D2: Taxonomy Mapping Strategy

**Chọn: Hard cut + backfill migration**

Topics cũ → topics mới qua mapping dict. Insight cũ được backfill bằng Alembic data migration (Python script). Frontend render trực tiếp string từ DB (không translate enum).

Mapping:
| Cũ | Mới |
|----|-----|
| Trí tuệ nhân tạo | AI/ML Ứng dụng hoặc AI/ML Nghiên cứu |
| Công nghệ | DevTools & Frameworks |
| Dữ liệu | Data Engineering |
| An ninh mạng | Security & Compliance |
| Pháp lý/Tuân thủ | Legal & Regulation |
| Quy trình phần mềm | Software Architecture |
| Nội dung/Marketing | (giữ nguyên — loại bớt nếu noise) |
| Dịch vụ/Nền tảng | Platform & API |
| Thị trường/Đối thủ | Market & Competition |
| Quản trị nội bộ | Team & Process |

**Note:** Mapping "Trí tuệ nhân tạo" → 2 categories cần heuristic (paper → Nghiên cứu, tool/SDK → Ứng dụng). Backfill script dùng keyword matching trên title.

### D3: Actionability Score Formula

```
score = 0.30 × gate_score
      + 0.15 × confidence
      + 0.20 × trust_score
      + 0.25 × event_weight
      + 0.10 × recency_factor
```

Trong đó:
- `gate_score`: từ Pass 1 (0-1)
- `confidence`: từ Gemini deep analysis (0-1)
- `trust_score`: từ source trust tier (0-1, đã có)
- `event_weight`: lookup table theo event_type (0-1)
- `recency_factor`: `max(0, 1 - age_days/30)` — tin 1 ngày tuổi = 0.97, 30 ngày = 0

### D4: Intelligence Tier Assignment

Rule-based (không dùng LLM):
- **Tactical**: event_type ∈ {Breaking Change, Cảnh báo bảo mật, Sự cố vận hành} AND actionability ≥ 0.7
- **Operational**: event_type ∈ {Phát hành mới, Ngừng hỗ trợ, Hướng dẫn/Best Practice} AND actionability ≥ 0.5
- **Strategic**: event_type ∈ {Tín hiệu xu hướng, Thay đổi chính sách, Cập nhật quy định} AND actionability ≥ 0.4
- **Informational**: mọi trường hợp còn lại

### D5: Gate Prompt Design

```
Bạn là AI triage agent. Đánh giá nhanh bài viết: đây là tin MỚI CÓ ÍCH cho team phần mềm hay chỉ là noise?

Trả JSON: { actionability_score: 0-1, content_type: "practical|strategic|theoretical|noise", gate_reason: "...", pass_gate: true/false }

Tiêu chí practical (score ≥ 0.7): phát hành tool/SDK, breaking change, security patch, benchmark có số liệu
Tiêu chí strategic (score 0.4-0.7): xu hướng dài hạn, policy change, regulation
Tiêu chí theoretical (score 0.2-0.4): paper nghiên cứu, opinion, chưa có sản phẩm
Tiêu chí noise (score < 0.2): PR/marketing, M&A không liên quan, tin cũ rehash

TIÊU ĐỀ: {title}
NỘI DUNG (trích): {content[:2000]}
```

Max output: 200 tokens. Temperature: 0.0 (deterministic).

### D6: New AnalysisResult Fields

Thêm vào `AnalysisResult` dataclass:
- `so_what: str | None` — 1 câu "bài này thay đổi gì cho team?"
- `adoption_ring: str | None` — Adopt/Trial/Assess/Hold
- `practical_indicators: dict | None` — JSON flags

Thêm `GateResult` dataclass mới:
- `actionability_score: float`
- `content_type: str`
- `gate_reason: str`
- `pass_gate: bool`

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Gate prompt quá aggressive → filter bài tốt | Threshold mặc định 0.4, configurable via `settings.gate_threshold`. Manual review queue cho bài gần threshold (0.3-0.5). |
| Backfill migration sai mapping cho insight cũ | Run trên staging trước. Mapping ambiguous (AI → 2 cats) fallback về "AI/ML Ứng dụng". |
| Frontend crash khi nhận topic cũ chưa backfill | Frontend render trực tiếp string, không validate enum → không crash. Badge color fallback xám. |
| Gemini hallucinate adoption_ring | Rule-based validate: chỉ chấp nhận Adopt/Trial/Assess/Hold, else null. |
| Daily cap bị tiêu nhanh hơn (2 calls/doc thay vì 1) | Gate call rất rẻ (200 tokens). Net token consumption giảm vì ~40-55% docs skip deep call. |

## Migration Plan

### Rollout sequence
1. Alembic migration: thêm 5 cột mới (nullable) — zero downtime
2. Deploy backend với two-pass pipeline + taxonomy mới
3. Run backfill script cho insight cũ: map topics, tính actionability_score cho existing insights (dùng default gate_score=0.5)
4. Deploy frontend với filter mới + tier badges
5. Monitor 1 tuần: kiểm tra gate filter rate, false positive rate

### Rollback
- Feature flag `ENABLE_GATE=true/false` trong settings — nếu gate có vấn đề, tắt flag → quay lại single-pass
- Cột mới nullable → backward compatible, frontend hiện old UI nếu fields null
- Taxonomy mapping one-way (không cần rollback — old values vẫn render được)
