## Context

Pipeline chạy tay, chưa scheduler. Hai lỗ rò quota Gemini được xác nhận trực tiếp trên code + DB (2026-07-07):

1. **Daily cap đếm trong RAM.** `_daily_counter` (`analyzer.py:19`) là dict module-level → reset về 0 mỗi tiến trình. Vì `run_analysis` chạy như process riêng mỗi lần → mỗi lần chạy được cấp lại full 500. Cap ~vô hiệu khi chạy >1 lần/ngày.
2. **Cap chỉ đếm khi tạo được insight** (`analyzer.py:383`, trong nhánh `if created`). Doc bị gate loại (`low_signal`) hay `failed` vẫn tốn ≥1 gate call nhưng **không** tính vào cap → cap under-count nặng.

Ngoài ra: dedup fingerprint (`exists_by_fingerprint`, không lọc status) **đang chạy đúng** — 0 URL trùng trong DB. Vấn đề "phân tích lại" thực chất là (a) backlog `pending` tin cũ phân tích lần đầu, và (b) 172/392 doc `pending` thiếu `published_at` bị kẹt cuối hàng đợi sau khi T3 thêm `NULLS LAST`.

Module ảnh hưởng: **M2 Ingestion**, **M3 Normalization**, **M4 AI Analysis**, **M5 Insight Repository**.

## Goals / Non-Goals

**Goals:**
- Cap 500/ngày thực sự chặn, đúng xuyên nhiều tiến trình, đếm mọi lần gọi Gemini (kể cả gate-reject/failed).
- Không doc nào kẹt cuối hàng đợi vì thiếu ngày; không phân tích bài > 6 tháng.
- Purge dữ liệu > 6 tháng mà **không** cho phân tích lại sau re-crawl.
- Pipeline tự chạy 2–4 lần/ngày, không bị 429/403.

**Non-Goals:**
- Không đổi logic gate/classify/urgency (W4). Không thêm nguồn (W2). Không CloakBrowser (W3).
- Không hard-delete. Không distributed lock/queue (1 dev, đơn tiến trình).

## Decisions

### D1 — Persist daily cap qua cột `analyzed_at`
Thêm `raw_documents.analyzed_at TIMESTAMP NULL`, set khi doc đạt trạng thái terminal (`analyzed` | `low_signal` | `failed`). Daily count = `COUNT(*) WHERE analyzed_at::date = today`.
- *Vì sao:* self-healing (không drift), sống sót restart, đếm **mọi** doc tốn Gemini (sửa luôn lỗ #2), không cần bảng counter riêng.
- *Alternatives:* (a) bảng counter tăng thủ công — bỏ (race, dễ lệch); (b) đếm `insights.created_at` — bỏ (bỏ sót low_signal/failed).
- Semantics cap = **số doc xử lý/ngày** (giữ như hiện tại). Lưu ý mỗi doc = 1 gate + (nếu qua) 1 deep → số Gemini call thực tế ≤ 2×cap (xem Risks).

### D2 — Gán crawl-date cho doc thiếu ngày
Trong `IngestionService.run()` trước khi `create()`: `published_at = entry.published_at or now(UTC)`. Tập trung 1 chỗ (không rải theo connector).
- *Vì sao:* gỡ kẹt hàng đợi (`NULLS LAST` của T3 hết tác dụng phụ), doc GitHub/HF vốn "đang hot" → gán ngày crawl đúng bản chất. Dedup giữ fingerprint ⇒ crawl lại không đổi ngày (ổn định).
- Backfill 172 doc `pending` hiện có: `UPDATE ... SET published_at = fetched_at WHERE published_at IS NULL`.

### D3 — Freshness gate 6 tháng tại ingestion
Bỏ qua (không lưu) doc có `published_at < now() - 6 tháng`. Config `max_age_months=6`, override per-source qua `Source.config`.
- *Vì sao:* chặn tại cửa rẻ nhất (chỉ so ngày, **0 Gemini call**). Doc thiếu ngày đã thành "hôm nay" (D2) nên luôn qua. Không cần tombstone cho freshness-reject vì re-check chỉ tốn phép so ngày.

### D4 — Retention TTL 6 tháng kiểu tombstone
Job/script purge: với insight/doc có `published_at < now() - 6 tháng` → set `insights.status='expired'`, NULL `raw_content`/`normalized_content`, set `raw_documents.status='expired'`, **GIỮ `fingerprint`**.
- *Vì sao:* `raw_documents` trở thành "sổ đã xử lý" bất tử; `exists_by_fingerprint` không cần content ⇒ crawl lại bài > 6 tháng vẫn skip, **không phân tích lại**. FK `insight→raw_documents` không cascade ⇒ xử lý Insight trước (đúng thứ tự tombstone).
- *Alternatives:* bảng `seen_fingerprints` riêng — bỏ (thừa; giữ row raw_document đơn giản & FK-safe).

### D5 — Scheduler: APScheduler in-process
Chạy trong FastAPI lifespan, `AsyncIOScheduler`, 3 mốc/ngày, jitter/delay giữa các source. Bật/tắt qua flag `ENABLE_SCHEDULER`.
- *Vì sao:* stack đã chọn APScheduler, 1 dev, không cần Redis/sidecar. Cap giờ ở DB (D1) nên chọn in-process an toàn, không lệ thuộc RAM.
- *Alternatives:* cron sidecar gọi `python -m` — bỏ (thêm container; và từng dựa vào cap-RAM giờ đã bỏ).

## Risks / Trade-offs

- **APScheduler chạy 2 lần dưới `uvicorn --reload`** → mitigate: chỉ start scheduler khi `ENABLE_SCHEDULER=true` (tắt ở dev/reload), `max_instances=1` + `coalesce=True`.
- **Cap đếm doc, không đếm Gemini call** (gate+deep ≤ 2 call/doc) → call thực có thể tới ~2×500 → mitigate: nếu vẫn rò, hạ `max_daily_analysis` hoặc đổi cap sang đếm call (Open Q).
- **Vẫn 429/403 dù jitter** → exponential backoff + `delay` per-source config.
- **Freshness/crawl-date coi nhầm bài cũ là mới** → chấp nhận (6 tháng rộng; dedup giữ ổn định).
- **Purge NULL content** ⇒ không regenerate được insight đã expired → chấp nhận (đã 6 tháng); fingerprint giữ ⇒ không re-analyze.

## Migration Plan

1. Alembic: `ADD COLUMN raw_documents.analyzed_at TIMESTAMP NULL`. (`status` là `String(20)`, không enum → thêm giá trị `expired` không cần migration.)
2. Backfill: `published_at = fetched_at` cho 172 doc NULL; set `analyzed_at = updated_at` cho doc đã terminal (khởi tạo cap cho hôm nay ~0 do updated_at cũ).
3. Deploy scheduler sau flag `ENABLE_SCHEDULER=false`; bật khi đã verify manual run + cap 2 ngày liên tiếp.
4. **Rollback:** tắt flag scheduler; cột `analyzed_at` vô hại; tombstone là soft (có thể un-`expired`).

## Open Questions

- Cap theo **doc** hay theo **Gemini call**? Mặc định giữ doc; revisit nếu quota vẫn rò.
- Giờ chạy scheduler cụ thể (vd 07:00/13:00/19:00 VN) — để operator cấu hình.
- Purge chạy hằng ngày hay hằng tuần (mặc định đề xuất: hằng ngày, cùng scheduler).
