## 1. Dependencies

- [ ] 1.1 Thêm `scikit-learn` vào `backend/requirements.txt`
- [ ] 1.2 Rebuild Docker image

## 2. Database Migration

- [ ] 2.1 Tạo migration `003_add_cluster_fields.py` — thêm `cluster_id` (UUID nullable) và `is_primary` (Boolean default true) vào bảng `insights`
- [ ] 2.2 Tạo index trên `cluster_id` (partial index WHERE cluster_id IS NOT NULL)
- [ ] 2.3 Chạy migration: `alembic upgrade head`

## 3. Model & Schema

- [ ] 3.1 Cập nhật `backend/app/models/insight.py` — thêm `cluster_id` và `is_primary` columns
- [ ] 3.2 Cập nhật `backend/app/schemas/insight.py` — thêm `cluster_id`, `is_primary`, `references` vào response schema

## 4. Dedup Engine

- [ ] 4.1 Tạo `backend/app/services/dedup_engine.py` — `DeduplicationEngine` class
- [ ] 4.2 Implement `find_clusters()` — TF-IDF vectorization + cosine similarity matrix
- [ ] 4.3 Implement `select_primary()` — chọn primary theo trust_tier > published_at > confidence
- [ ] 4.4 Implement `run_dedup()` — orchestrate: lấy new insights + existing 7 ngày → cluster → update DB

## 5. Pipeline Integration

- [ ] 5.1 Tích hợp `DeduplicationEngine.run_dedup()` vào cuối `IngestionService.run()` (sau analysis)
- [ ] 5.2 Hoặc tạo script riêng `run_dedup.py` để chạy thủ công

## 6. API & Repository

- [ ] 6.1 Cập nhật `insight_repo.py` — filter `is_primary=true` cho list, query references cho detail
- [ ] 6.2 Cập nhật `routes/insights.py` — detail endpoint trả kèm `references` array

## 7. Frontend

- [ ] 7.1 Cập nhật `types/insight.ts` — thêm `cluster_id`, `is_primary`, `references` fields
- [ ] 7.2 Cập nhật `InsightDetail.tsx` — hiển thị section "Bài viết liên quan" khi có references

## 8. Documentation

- [ ] 8.1 Đọc toàn bộ `docs/system_overview.md` và cập nhật chính xác: thêm dedup engine vào pipeline, mô tả cluster model, cập nhật schema insights

## 9. Verification

- [ ] 9.1 Chạy migration — verify cột mới trong DB
- [ ] 9.2 Tạo 2+ insights về cùng sự kiện (khác source) → verify cluster được tạo
- [ ] 9.3 API list → verify chỉ hiện primary insights
- [ ] 9.4 API detail → verify references array có insights liên quan
- [ ] 9.5 Frontend → verify "Bài viết liên quan" section hiển thị đúng
