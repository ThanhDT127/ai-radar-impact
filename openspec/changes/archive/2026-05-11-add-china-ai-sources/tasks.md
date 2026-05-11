## 1. Schema Migration

- [x] 1.1 Tạo Alembic migration thêm 2 cột vào `sources`: `region VARCHAR(20) NOT NULL DEFAULT 'global'`, `target_roles VARCHAR(50)[] NOT NULL DEFAULT '{}'`
- [x] 1.2 Trong migration data step: backfill `region='vietnam'` cho `VnExpress Số hóa`
- [x] 1.3 Trong migration data step: backfill `target_roles` cho 18 sources cũ theo topic match (best effort)
- [x] 1.4 Chạy migration trên dev DB và verify

## 2. Update Source Model & Schemas

- [x] 2.1 Cập nhật `backend/app/models/source.py` thêm `region` và `target_roles` attributes
- [x] 2.2 Cập nhật `backend/app/schemas/source.py` Pydantic schemas thêm 2 fields
- [x] 2.3 Cập nhật `backend/app/routes/admin.py` (nếu admin-api expose Source) — response trả thêm 2 fields

## 3. Verify Feed URLs

- [x] 3.1 Tạo `backend/app/scripts/verify_feeds.py` — chấp nhận list URLs, chạy parallel `feedparser.parse`, output JSON {url, status, num_entries, sample_title}
- [x] 3.2 Chạy verify cho 10 nguồn Trung Quốc + analyst, lưu kết quả
- [x] 3.3 Đối với URL không trả entries: thử endpoint thay thế (vd HF papers RSS, Substack /feed) hoặc loại khỏi batch

## 4. Update Seed Sources

- [x] 4.1 Cập nhật `backend/app/scripts/seed_sources.py` thêm 8 nguồn China AI (DeepSeek, Qwen, GLM, Yi, Kimi, Hunyuan, MiniMax, Baichuan) với feed URL đã verify
- [x] 4.2 Thêm 2 newsletters: Interconnects (`https://www.interconnects.ai/feed`), ChinaTalk (`https://www.chinatalk.media/feed`)
- [x] 4.3 Set `region="china"` cho tất cả 10 sources mới
- [x] 4.4 Set `target_roles` phù hợp: AI labs → `[Engineering, Data/AI]`; newsletters → `[Executive, Engineering, Data/AI]`
- [x] 4.5 Set `trust_tier`:
  - `very_high`: DeepSeek, Qwen, GLM
  - `high`: Yi, Kimi, Hunyuan, MiniMax, Baichuan, Interconnects, ChinaTalk
- [x] 4.6 Set `topics` phù hợp với taxonomy hiện có (`Trí tuệ nhân tạo`, có thể thêm `Dữ liệu` cho papers)

## 5. Run Seed & Verify Ingestion

- [x] 5.1 Chạy `docker-compose exec backend python -m app.scripts.seed_sources` — 10 sources mới được tạo
- [x] 5.2 Chạy `docker-compose exec backend python -m app.scripts.run_ingestion` — verify ít nhất 5/10 nguồn TQ trả entries
- [x] 5.3 Spot check 1 raw_document từ DeepSeek: title/content có nội dung thực, fingerprint generated, không lỗi parse
- [x] 5.4 Verify analyzer xử lý được: `run_analysis` không lỗi với content tiếng Anh từ HF/Substack

## 6. Documentation

- [x] 6.1 Cập nhật `docs/system_overview.md` Section 3.1 — note layer "China AI" và 2 newsletters
- [x] 6.2 Cập nhật `CLAUDE.md` — thêm `region` field vào "Source schema" section
- [x] 6.3 Cập nhật `docs/specs/07_source_strategy_and_source_catalog_v_1.md` (nếu tồn tại) — thêm China AI cluster

## 7. Verification

- [x] 7.1 Sau 24h ingestion: query DB count insights theo `region` — China có insights ≠ 0
- [x] 7.2 Spot-check 3-5 insights TQ — chất lượng phân tích AI không tệ hơn nguồn US (signal về tin TQ chính xác)
- [x] 7.3 Nếu một số HF org RSS không hoạt động: document trong tasks và defer cho `expand-source-coverage-2a` hoặc tạo change riêng cho HF API polling
