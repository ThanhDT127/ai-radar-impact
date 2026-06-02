## Why

Dashboard AI Radar hiện tại surface quá nhiều bài không thiết thực: nghiên cứu học thuật, tin M&A không liên quan tech, opinion pieces. Nguyên nhân gốc: taxonomy phẳng ("Trí tuệ nhân tạo", "Công nghệ" quá rộng), event types thiếu loại quan trọng nhất cho dev ("Breaking Change", "Benchmark"), và không có cơ chế phân tầng nội dung (tactical vs strategic). Cần overhaul toàn bộ taxonomy + thêm pre-screening gate + actionability scoring để AI Radar trở thành công cụ **developer-centric intelligence** thay vì news aggregator.

## What Changes

### **BREAKING** — Taxonomy Topics
- Thay 10 topics cũ (generic) bằng 12 topics developer-centric: `AI/ML Ứng dụng`, `AI/ML Nghiên cứu`, `DevTools & Frameworks`, `Cloud & Infrastructure`, `Data Engineering`, `Security & Compliance`, `Software Architecture`, `Developer Experience`, `Platform & API`, `Market & Competition`, `Legal & Regulation`, `Team & Process`
- Frontend label render trực tiếp từ `insight.topics` → cần update component

### **BREAKING** — Event Types mở rộng
- Thêm 3 event types mới: `Breaking Change`, `Benchmark/So sánh`, `Hướng dẫn/Best Practice`
- Gộp `Ngừng hỗ trợ` → `Ngừng hỗ trợ/Deprecation` (rename)
- Thêm `Nghiên cứu/Paper` (tách từ `Cập nhật nghiên cứu`, rõ ràng hơn)
- Cập nhật `IMPACT_LABEL_MAP` và thêm `EVENT_TYPE_WEIGHTS`

### Two-Pass Analysis Pipeline (mới)
- **Pass 1 — Gate**: prompt nhẹ (~200 tokens) quyết định bài có đáng phân tích sâu không, trả `actionability_score` (0-1), `content_type` (practical/strategic/theoretical/noise)
- **Pass 2 — Deep Analysis**: prompt hiện tại (cải tiến) chỉ chạy cho bài qua gate (actionability ≥ 0.4)
- Bài bị filter ở gate gán `status='low_signal'` hoặc `status='noise'`

### Actionability Score (mới)
- Composite formula: Gate score (30%) + Confidence (15%) + Trust (20%) + Event weight (25%) + Recency (10%)
- Thêm cột `actionability_score FLOAT` vào bảng `insights`

### Intelligence Tier — Content Stratification (mới)
- Phân tầng insight: `tactical` (hành động ngay), `operational` (plan cần thiết), `strategic` (xu hướng dài hạn), `informational` (đọc cho biết)
- Rule-based từ event_type + actionability_score + affected_roles
- Thêm cột `intelligence_tier VARCHAR(20)` vào bảng `insights`

### Enhanced Prompt
- Thêm `so_what` field — 1 câu trả lời "bài này thay đổi gì cho team?"
- Thêm `adoption_ring` — Adopt/Trial/Assess/Hold (ThoughtWorks-inspired)
- Thêm `practical_indicators` — JSON flags: has_code_example, has_benchmark, has_api_change, has_migration_guide, has_security_patch

## Capabilities

### New Capabilities
- `content-gate`: Pre-screening gate sử dụng Gemini Flash prompt nhẹ, trả actionability_score và content_type, filter bài noise trước deep analysis
- `actionability-scoring`: Composite actionability score tính từ 5 yếu tố (gate, confidence, trust, event weight, recency) để rank insight theo mức độ cần hành động
- `intelligence-tier`: Phân tầng nội dung thành tactical/operational/strategic/informational dựa trên event type, actionability score, và affected roles

### Modified Capabilities
- `ai-analysis`: **BREAKING** — Taxonomy topics thay đổi từ 10 → 12, event types từ 9 → 11, thêm 5 output fields mới (so_what, adoption_ring, practical_indicators, actionability_score, intelligence_tier). ANALYSIS_PROMPT được viết lại. Gate prompt được thêm mới.
- `semantic-dedup`: Cập nhật `_VN_SPECIFIC_TOPICS` để match topics mới
- `insight-api`: API response thêm 4 trường mới (actionability_score, intelligence_tier, so_what, adoption_ring). Hỗ trợ filter theo intelligence_tier
- `dashboard-actionable-filters`: Frontend filter thêm intelligence_tier dropdown, sort by actionability_score

## Impact

### Backend
- `app/ai/prompts.py` — Viết lại taxonomy + thêm GATE_PROMPT + sửa ANALYSIS_PROMPT
- `app/ai/gemini_client.py` — Thêm `gate_analyze()` method + thêm fields mới vào AnalysisResult
- `app/services/analyzer.py` — Two-pass pipeline flow, composite scoring, intelligence tier logic
- `app/models/insight.py` — Thêm 5 cột: actionability_score, intelligence_tier, so_what, adoption_ring, practical_indicators
- `app/repositories/insight_repo.py` — Cập nhật create() với fields mới
- `app/routes/insights.py` — Filter params mới
- Alembic migration cho schema changes

### Frontend
- `InsightCard.tsx` — Render intelligence_tier badge, topics mới
- `InsightDetail.tsx` — Hiển thị so_what, adoption_ring, practical_indicators
- `InsightList.tsx` — Filter dropdown cho intelligence_tier, sort by actionability_score
- Types và API calls cần update

### Dependencies
- Không thêm dependency Python mới (Gemini API đã có)
- Không thay đổi database engine (PostgreSQL unchanged)
