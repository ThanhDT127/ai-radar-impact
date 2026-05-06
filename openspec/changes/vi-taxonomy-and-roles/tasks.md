## 1. Backend — Taxonomy tiếng Việt (P1)

- [x] 1.1 Sửa `backend/app/ai/prompts.py` — đổi `ALLOWED_TOPICS` sang tiếng Việt (10 giá trị)
- [x] 1.2 Sửa `prompts.py` — đổi `ALLOWED_EVENT_TYPES` sang tiếng Việt (9 giá trị)
- [x] 1.3 Sửa `prompts.py` — đổi `ALLOWED_NATURES` sang tiếng Việt (5 giá trị)
- [x] 1.4 Sửa `prompts.py` — thêm `ALLOWED_ROLES` list (8 giá trị theo spec 02_frd section 6.7)
- [x] 1.5 Sửa `prompts.py` — viết lại `ANALYSIS_PROMPT` bằng tiếng Việt, thêm field `affected_roles` vào JSON schema
- [x] 1.6 Sửa `prompts.py` — cập nhật `build_prompt()` thêm param `roles` và format vào prompt
- [ ] 1.7 Verify: chạy `run_analysis` với 1 document → output JSON có topics/summary tiếng Việt + affected_roles

## 2. Backend — Data model & Migration (P1)

- [x] 2.1 Sửa `backend/app/models/insight.py` — thêm column `affected_roles: ARRAY(String)`
- [x] 2.2 Sửa `backend/app/models/insight.py` — thêm column `published_at: DateTime nullable`
- [x] 2.3 Tạo migration: `alembic revision 002_add_affected_roles_and_published_at`
- [x] 2.4 Chạy migration: `alembic upgrade head` — verify 2 columns mới trong bảng insights
- [ ] 2.5 Verify: query bảng insights thấy columns `affected_roles` và `published_at`

## 3. Backend — Analyzer service update (P1)

- [x] 3.1 Sửa `backend/app/services/analyzer.py` — parse `affected_roles` từ Gemini response
- [x] 3.2 Sửa `analyzer.py` — gán `published_at` từ `raw_document.published_at`
- [x] 3.3 Sửa `analyzer.py` — đổi impact_label mapping sang tiếng Việt ("Nghiêm trọng", "Cao", "Trung bình", "Thấp", "Theo dõi")
- [ ] 3.4 Verify: chạy full pipeline → insights mới có `affected_roles` populated và `published_at` có giá trị

## 4. Backend — API schemas & routes (P1)

- [x] 4.1 Sửa `backend/app/schemas/insight.py` — thêm `affected_roles: list[str]` và `published_at: datetime | None`
- [x] 4.2 Sửa `backend/app/routes/insights.py` — thêm query params: `role: str | None`, `sort_by: str = "created_at"`
- [x] 4.3 Sửa `backend/app/repositories/insight_repo.py` — thêm filter `affected_roles.any(role)` và sort theo `published_at`, `impact_label`
- [ ] 4.4 Verify: `GET /api/v1/insights?role=Engineering` → chỉ trả insights có role Engineering
- [ ] 4.5 Verify: `GET /api/v1/insights?sort_by=published_at` → sorted đúng thứ tự

## 5. Frontend — Labels tiếng Việt & Types (P1)

- [x] 5.1 Sửa `frontend/src/types/insight.ts` — thêm `affected_roles: string[]` và `published_at: string | null`
- [x] 5.2 Sửa `frontend/src/api/insights.ts` — thêm optional params `role`, `source_id`, `sort_by`
- [x] 5.3 Sửa `frontend/src/pages/InsightList.tsx` — đổi labels sang tiếng Việt
- [x] 5.4 Sửa `frontend/src/pages/InsightDetail.tsx` — labels tiếng Việt, hiển thị published_at và affected_roles
- [ ] 5.5 Sửa `frontend/src/components/Layout.tsx` — header tiếng Việt
- [x] 5.6 Sửa `frontend/src/components/ImpactBadge.tsx` — cập nhật mapping cho impact labels tiếng Việt
- [x] 5.7 Sửa `frontend/src/components/InsightCard.tsx` — hiển thị published_at, roles badges, event tags
- [ ] 5.8 Verify: mở browser → UI hiển thị tiếng Việt, insight cards có roles và thời gian publish

## 6. End-to-End Verification (P1)

- [ ] 6.1 Chạy full pipeline: ingestion → analysis → verify insights mới có tiếng Việt + roles + published_at
- [ ] 6.2 Gọi API với filter role → response đúng
- [ ] 6.3 Gọi API với sort_by → thứ tự đúng
- [ ] 6.4 Mở browser → verify UI tiếng Việt, impact badges đúng màu
