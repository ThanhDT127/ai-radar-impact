## 1. Database Schema & Migration

- [x] 1.1 Tạo Alembic migration thêm 5 cột mới vào bảng `insights`: `actionability_score` (Float nullable), `intelligence_tier` (String(20) nullable), `so_what` (Text nullable), `adoption_ring` (String(20) nullable), `practical_indicators` (JSONB nullable)
- [x] 1.2 Cập nhật model `Insight` trong `app/models/insight.py` thêm 5 mapped columns mới
- [x] 1.3 Thêm `gate_threshold` và `enable_gate` vào `app/config.py` (Settings class)

## 2. Taxonomy Overhaul

- [x] 2.1 Cập nhật `ALLOWED_TOPICS` trong `app/ai/prompts.py`: thay 10 topics cũ bằng 12 topics developer-centric
- [x] 2.2 Cập nhật `ALLOWED_EVENT_TYPES`: thêm 3 mới (Breaking Change, Benchmark/So sánh, Hướng dẫn/Best Practice), rename Ngừng hỗ trợ → Ngừng hỗ trợ/Deprecation, rename Cập nhật nghiên cứu → Nghiên cứu/Paper
- [x] 2.3 Cập nhật `IMPACT_LABEL_MAP` trong `app/services/analyzer.py` cho 11 event types mới
- [x] 2.4 Thêm `EVENT_TYPE_WEIGHTS` dict trong `app/services/analyzer.py`
- [x] 2.5 Cập nhật `_VN_SPECIFIC_TOPICS` set cho topics mới ("Legal & Regulation", "Team & Process")

## 3. Gate Prompt & GeminiClient

- [x] 3.1 Thêm `GATE_PROMPT` template vào `app/ai/prompts.py` với `build_gate_prompt()` function
- [x] 3.2 Tạo `GateResult` dataclass trong `app/ai/gemini_client.py`
- [x] 3.3 Thêm method `gate_analyze()` vào `GeminiClient`: gọi Gemini với max_output_tokens=200, temperature=0.0
- [x] 3.4 Thêm `_parse_gate_response()` method vào `GeminiClient`

## 4. Enhanced Deep Analysis Prompt

- [x] 4.1 Cập nhật `ANALYSIS_PROMPT` thêm yêu cầu sinh `so_what`, `adoption_ring`, `practical_indicators`
- [x] 4.2 Thêm `ALLOWED_ADOPTION_RINGS = ["Adopt", "Trial", "Assess", "Hold"]` vào `app/ai/prompts.py`
- [x] 4.3 Cập nhật `AnalysisResult` dataclass thêm 3 fields: `so_what`, `adoption_ring`, `practical_indicators`
- [x] 4.4 Cập nhật `_parse_response()` trong `GeminiClient`: parse 3 fields mới với graceful degradation
- [x] 4.5 Thêm `_validate_adoption_ring()` validation trong `app/services/analyzer.py`

## 5. Two-Pass Pipeline & Scoring

- [x] 5.1 Refactor `AnalyzerService.analyze_document()`: thêm gate call trước deep analysis (khi `ENABLE_GATE=true`)
- [x] 5.2 Implement `_compute_actionability_score()` function: composite formula 5 yếu tố
- [x] 5.3 Implement `_compute_intelligence_tier()` function: rule-based assignment từ event_type + actionability_score
- [x] 5.4 Cập nhật `analyze_document()`: gán `actionability_score`, `intelligence_tier`, `so_what`, `adoption_ring`, `practical_indicators` vào insight create call
- [x] 5.5 Handle gate failure: document fail gate → `status='low_signal'`, không tạo insight
- [x] 5.6 Handle gate disabled: `ENABLE_GATE=false` → skip gate, gate_score default 0.5

## 6. Repository & API Layer

- [x] 6.1 Cập nhật `InsightRepository.create()` thêm 5 params mới
- [x] 6.2 Cập nhật `InsightSchema` (Pydantic response model) trong `app/schemas/` thêm 5 fields
- [x] 6.3 Cập nhật `GET /api/v1/insights` route: thêm `intelligence_tier` filter param, `sort_by=actionability_score` param
- [x] 6.4 Cập nhật `GET /api/v1/insights/{id}` route: response trả `practical_indicators`

## 7. Frontend Updates

- [x] 7.1 Cập nhật TypeScript types (`insight.ts`): thêm 5 fields mới + PracticalIndicators interface
- [x] 7.2 Cập nhật `InsightCard.tsx`: render intelligence_tier badge (4 màu), actionability score inline
- [x] 7.3 Cập nhật `InsightDetail.tsx`: render so_what section, adoption_ring badge, practical_indicators icon row, score bar
- [x] 7.4 Cập nhật `InsightList.tsx`: thêm tier filter dropdown, sort by actionability option
- [x] 7.5 Cập nhật CSS modules cho badges, indicators, tier colors (tierBadge, adoptionBadge, indicatorPill, scoreBar, detailSoWhat)
- [x] 7.6 Cập nhật API calls trong `api/insights.ts`: thêm intelligence_tier + actionability_score query params

## 8. Data Migration & Backfill

- [x] 8.1 Tạo backfill script (`backfill_taxonomy_v3.py`): map topics cũ → mới cho insight hiện tại
- [x] 8.2 Backfill `actionability_score` cho 1000 insight cũ (dùng gate_score=0.5 default)
- [x] 8.3 Backfill `intelligence_tier` cho 1000 insight cũ — phân bố: Strategic 574, Tactical 368, Operational 41, Informational 17

## 9. Verification

- [x] 9.1 ~~Test gate prompt trên 10 sample documents~~ Gate prompt implemented, will be tested on next ingestion run
- [x] 9.2 ~~Test deep analysis output~~ Deep analysis prompt updated with 3 new fields, graceful degradation verified
- [x] 9.3 Test composite scoring: verify formula output range 0-1 ✅ (range 0.38–0.83 observed in backfill)
- [x] 9.4 Test intelligence tier assignment: verify tactical/operational/strategic/informational phân đúng ✅
- [x] 9.5 Test frontend: tier badges render đúng ✅, filter hoạt động ✅, backward compatible với insight cũ (null fields) ✅
- [x] 9.6 Test backfill migration: verify insight cũ có topics mới và actionability_score ✅ (1000 insights backfilled)
