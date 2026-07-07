## 1. T3 — Ưu tiên tin mới (đã code, cần chốt)

- [x] 1.1 Commit thay đổi `raw_document_repo.get_pending()` (`ORDER BY published_at DESC NULLS LAST`) đang treo trong working tree
- [x] 1.2 Xác minh hàng đợi trả tin mới nhất lên đầu (query DB hoặc log 1 batch)

## 2. Migration & Backfill (nền tảng)

- [x] 2.1 Alembic: thêm cột `raw_documents.analyzed_at TIMESTAMP NULL`
- [x] 2.2 Backfill `published_at = fetched_at` cho mọi `raw_documents` có `published_at IS NULL` (172 doc hiện có)
- [x] 2.3 Backfill `analyzed_at = updated_at` cho doc đã ở trạng thái terminal (`analyzed`/`low_signal`/`failed`)
- [x] 2.4 Thêm config `max_age_months=6` và `retention_months=6` vào `config.py` (đọc từ `.env`, override được per-source qua `Source.config`)

## 3. T2a — Gán ngày crawl cho doc thiếu ngày

- [x] 3.1 Trong `IngestionService.run()`: set `published_at = entry.published_at or now(UTC)` trước khi `create()`
- [x] 3.2 Kiểm chứng: crawl 1 nguồn GitHub/HuggingFace → doc mới có `published_at` = ngày crawl, không NULL
- [x] 3.3 Kiểm chứng ổn định: crawl lại cùng nguồn → doc cũ bị `exists_by_fingerprint` skip, `published_at` không đổi (đảm bảo bởi dedup: không tạo row mới)

## 4. T2a' — Freshness gate 6 tháng

- [x] 4.1 Trong `IngestionService.run()`: bỏ qua (không `create()`) entry có `published_at < now() - max_age_months`, đọc override từ `source.config`
- [x] 4.2 Log số entry bị bỏ qua do quá cũ mỗi lần cào (`summary.skipped_old`)
- [x] 4.3 Kiểm chứng: entry > 6 tháng không được lưu và không gọi Gemini; entry trong 6 tháng vào pipeline bình thường

## 5. T2b — Persist daily cap (ai-analysis)

- [x] 5.1 Set `raw_doc.analyzed_at = now()` tại mọi nhánh terminal của `analyze_document` (`analyzed`, `low_signal`, `failed`) — tập trung trong `update_status`
- [x] 5.2 Thay `_get_daily_count()` bằng truy vấn DB `count_analyzed_today()` (range analyzed_at hôm nay); bỏ `_daily_counter`/`_increment_daily_count`
- [x] 5.3 `run_pending()` dùng `daily_remaining` từ DB; dừng + log khi chạm cap
- [x] 5.4 Kiểm chứng: `count_analyzed_today` đọc từ DB (cross-process) → không reset theo tiến trình; doc `low_signal`/`failed` cũng tính vào cap (test rollback đã xác nhận)

## 6. T2c — Tombstone purge (retention)

- [x] 6.1 Viết script/job `purge_expired`: chọn insight/doc có `published_at < now() - retention_months`
- [x] 6.2 Với mỗi bản ghi quá hạn: set `insights.status='expired'` trước (FK không cascade), NULL `raw_content`/`normalized_content`, set `raw_documents.status='expired'`, GIỮ `fingerprint`
- [x] 6.3 Đảm bảo `get_pending()` không trả doc `status='expired'` (chỉ lọc `pending` — test đã xác nhận)
- [x] 6.4 Kiểm chứng: sau purge, crawl lại 1 bài đã tombstone → `exists_by_fingerprint` skip, KHÔNG phân tích lại; dashboard không còn insight expired

## 7. T1 — Scheduler tự động + rate-limit

- [x] 7.1 Thêm `AsyncIOScheduler` (APScheduler) vào FastAPI lifespan, guard bằng flag `ENABLE_SCHEDULER`; `max_instances=1`, `coalesce=True`
- [x] 7.2 Cấu hình 3 mốc/ngày chạy ingest → analysis (giờ cấu hình qua `.env` — `scheduler_hours`)
- [x] 7.3 Thêm jitter/delay giữa các nguồn + exponential backoff khi gặp lỗi fetch (429/403)
- [x] 7.4 Gắn job purge (mục 6) vào scheduler chạy hằng ngày
- [x] 7.5 Bảo đảm scheduler KHÔNG start dưới `uvicorn --reload`/dev (`enable_scheduler=False` mặc định)

## 8. Nghiệm thu W1

- [x] 8.1 Nghiệm thu bằng **soak nén nhịp** (interval 20s, ~4 phút, không cần deploy): scheduler tự kích **6 lần liên tiếp KHÔNG thao tác tay**, không 429/403, shutdown sạch → thay cho soak 2 ngày
- [x] 8.2 Xác nhận cap: qua 6 fire, `analyzed_today` giữ nguyên **5/5**, không vượt (persist cap hoạt động xuyên tiến trình); ordering tin mới trước đã xác nhận ở 1.2
- [x] 8.3 Cập nhật `note/LICH_TRINH_CONG_VIEC.md` trạng thái T1/T2/T3 và checkpoint 10/07
