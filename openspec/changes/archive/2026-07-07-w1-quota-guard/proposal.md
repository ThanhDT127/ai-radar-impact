## Why

Pipeline hiện chạy tay (`run_ingestion`/`run_analysis`), chưa có scheduler nên phải thao tác thủ công mỗi ngày. Nghiêm trọng hơn: daily cap 500 tài liệu/ngày đang đếm bằng biến RAM (`_daily_counter` trong `analyzer.py`), **reset về 0 mỗi lần chạy process mới** → cap gần như vô hiệu, quota Gemini có thể vượt xa 500/ngày khi chạy nhiều lần. Đồng thời mỗi lần crawl nạp cả tin cũ (arXiv/feed backfill) và tin thiếu ngày (GitHub/HuggingFace — hiện 172/392 doc `pending` không có `published_at`) → tốn quota phân tích tin không còn giá trị. Phải đóng "van" quota **trước** khi bật scheduler tự động (nguyên tắc thứ tự W1).

## What Changes

- **Persist daily analysis cap vào DB** (đếm tài liệu đã xử lý theo ngày) thay cho counter RAM per-process. Cap thực sự chặn ở 500/ngày xuyên nhiều lần chạy.
- **Gán `published_at = ngày crawl`** cho doc thiếu ngày (thay vì để NULL) + backfill doc `pending` hiện có → không doc nào kẹt vĩnh viễn cuối hàng đợi.
- **Freshness gate 6 tháng**: bài `published_at` cũ hơn 6 tháng không vào pipeline phân tích. Trong vòng 6 tháng: không skip gì.
- **Retention tombstone 6 tháng**: quá 6 tháng → ẩn Insight + xóa content nặng (`raw_content`/`normalized_content`), **GIỮ `fingerprint` + `status='expired'`** → crawl lại sau đó không bị phân tích lại (dedup không thủng).
- **Scheduler tự động** ingest → analysis 2–4 lần/ngày + jitter/delay tránh 429/403.
- (Đã xong, cần **commit**) Xếp hàng đợi pending mới nhất trước (`published_at DESC NULLS LAST`).

## Capabilities

### New Capabilities
- `scheduled-ingestion`: chạy tự động pipeline ingest+analysis theo lịch 2–4 lần/ngày, có rate-limit/jitter để tránh bị chặn.
- `document-lifecycle`: vòng đời RawDocument về mặt quota — gán ngày (crawl-date fallback), lọc theo tuổi (freshness gate 6 tháng), dedup **giữ fingerprint bất tử**, và tombstone-purge khi hết TTL 6 tháng mà không cho phân tích lại.

### Modified Capabilities
- `ai-analysis`: daily analysis cap được persist qua DB, đúng xuyên nhiều tiến trình (không còn reset theo process).

## Non-goals

- Không đổi thuật toán phân loại/gate (`urgency`, độ chính xác gate → W4).
- Không thêm nguồn mới / rà arXiv catalog / GitHub weekly-monthly (→ W2).
- Không tích hợp CloakBrowser hay cookie refresh (→ W3).
- **Không hard-delete** dữ liệu — chỉ soft status (`expired`) + null content.
- Chưa làm distributed lock/queue; 1 developer, APScheduler đơn tiến trình là đủ.

## Impact

- **Phase:** Phase 1 (MVP vận hành). Không phụ thuộc Epic khác.
- **Code:** `services/ingestion.py`, `services/analyzer.py` (`_daily_counter`), `services/normalizer.py`, `repositories/raw_document_repo.py`, `repositories/insight_repo.py`; thêm scheduler (APScheduler, đã có trong tech stack) + script purge; config `retention_months=6` / `max_age_months=6` (override được per-source qua `Source.config`).
- **DB:** thêm giá trị status `expired` cho `raw_documents`; cột/bảng đếm cap theo ngày; migration Alembic.
- **Ràng buộc đã biết:** FK `insight.raw_document_id → raw_documents` không `ON DELETE CASCADE` → purge phải xử lý Insight trước (đã tính trong thiết kế tombstone).
