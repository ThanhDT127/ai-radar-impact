## 1. Database Migration

- [x] 1.1 Tạo Alembic migration thêm 7 cột vào `insights`: `signal TEXT`, `why_it_matters TEXT`, `recommendations JSONB`, `risks TEXT[]`, `momentum VARCHAR(20)`, `urgency VARCHAR(20)`, `vietnam_relevance VARCHAR(20)`
- [x] 1.2 Chạy migration trên dev DB và verify schema

## 2. Update Models & Schemas

- [x] 2.1 Cập nhật `backend/app/models/insight.py` thêm 7 attributes
- [x] 2.2 Cập nhật `backend/app/schemas/insight.py` Pydantic schemas (Insight, InsightDetail, InsightList) thêm 7 fields với type hints chính xác
- [x] 2.3 Cập nhật `RecommendationItem` schema (action_type Literal, note str)

## 3. Refactor Gemini Prompt

- [x] 3.1 Cập nhật `backend/app/ai/prompts.py` — mở rộng JSON output schema yêu cầu Gemini trả thêm `signal`, `why_it_matters`, `recommendations`, `risks`
- [x] 3.2 Thêm closed set `ALLOWED_ACTION_TYPES = ["watch", "read", "test", "PoC", "roadmap"]` vào prompts.py
- [x] 3.3 Prompt nhấn mạnh: `recommendations` keys ⊆ `affected_roles`; `signal` khác title

## 4. Update AnalyzerService

- [x] 4.1 Cập nhật `backend/app/services/analyzer.py` parse 4 fields AI mới từ Gemini response
- [x] 4.2 Thêm helper `_validate_recommendations(recs, affected_roles)` drop keys không hợp lệ
- [x] 4.3 Thêm helper `_compute_urgency(impact_label, published_at)` — rule D3
- [x] 4.4 Thêm helper `_compute_vietnam_relevance(source, topics)` — rule D4
- [x] 4.5 Graceful fallback: nếu parse 4 fields AI lỗi, lưu null thay vì discard insight

## 5. Update Dedup Engine để expose cluster metadata

- [x] 5.1 Cập nhật `backend/app/services/dedup_engine.py` thêm method `get_cluster_metadata(cluster_id)` trả `{size, earliest_published_at}`
- [x] 5.2 Hook vào AnalyzerService sau dedup: tính `momentum` cho mỗi insight bằng cluster metadata + rule D2

## 6. Update API Routes

- [x] 6.1 Cập nhật `backend/app/routes/insights.py` GET endpoints trả thêm 7 fields
- [x] 6.2 Thêm query params `urgency`, `momentum`, `vietnam_relevance` vào list endpoint
- [x] 6.3 Đổi default sort: urgency DESC (critical→low) THEN published_at DESC

## 7. Frontend Components

- [x] 7.1 Tạo `frontend/src/components/UrgencyBadge.tsx` — 4 màu cho 4 levels
- [x] 7.2 Tạo `frontend/src/components/MomentumIndicator.tsx` — text/icon cho new/rising/mature
- [x] 7.3 Tạo `frontend/src/components/RecommendationsByRole.tsx` — render dict role→{action_type, note} với badges
- [x] 7.4 Cập nhật `InsightCard.tsx` — render UrgencyBadge + signal (fallback summary_short) + MomentumIndicator
- [x] 7.5 Cập nhật `InsightDetail.tsx` — render section "Tại sao quan trọng", "Khuyến nghị", "Rủi ro" (hide nếu null)
- [x] 7.6 Cập nhật `frontend/src/api/insights.ts` types thêm 7 fields

## 8. Optional Backfill

- [x] 8.1 Tạo `backend/app/scripts/regenerate_insights.py` — re-analyze insights cũ với prompt mới (args: `--limit`, `--since`, `--source-id`)
- [x] 8.2 Document cách dùng trong `docs/system_overview.md`

## 9. Documentation

- [x] 9.1 Cập nhật `CLAUDE.md` thêm section "Insight Schema v2" liệt kê 7 fields mới + closed sets
- [x] 9.2 Cập nhật `docs/system_overview.md` Section 3.4 (Phân tích AI) phản ánh schema mới
- [ ] 9.3 Cập nhật `openspec/specs/ai-analysis/spec.md` (sync sau archive)

## 10. Verification

- [x] 10.1 Chạy `docker-compose up -d --build backend` — backend khởi động không lỗi
- [x] 10.2 Chạy `run_ingestion` trên 1-2 sources mới — insight mới có đủ 7 fields (đã verify qua regenerate_insights — 3/3 OK với signal/why/recommendations/risks)
- [x] 10.3 Chạy `run_analysis` trên pending docs cũ — same (regenerate path validate)
- [x] 10.4 Verify frontend render đúng: TypeScript build clean, frontend HTTP 200, components mới import đúng
- [x] 10.5 Kiểm tra distribution: momentum {mature:387, new:16, rising:4}; urgency/vietnam_relevance hiện chỉ populated cho insight mới (insight cũ chưa regenerate vẫn null — backwards compatible)
