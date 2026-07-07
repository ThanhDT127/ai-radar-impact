# document-lifecycle Specification

## Purpose
TBD - created by archiving change w1-quota-guard. Update Purpose after archive.
## Requirements
### Requirement: Gán ngày crawl cho tài liệu thiếu ngày xuất bản

Khi một tài liệu nạp vào không có `published_at` (ví dụ GitHub Trending, HuggingFace), hệ thống SHALL gán `published_at = thời điểm crawl` thay vì để NULL. Tài liệu đã lưu (dedup) SHALL giữ nguyên ngày của lần crawl đầu tiên.

#### Scenario: Doc thiếu ngày được gán ngày crawl

- **WHEN** connector trả entry không có `published_at`
- **THEN** `IngestionService` lưu doc với `published_at = now()` tại thời điểm ingest
- **AND** doc không còn bị đẩy xuống cuối hàng đợi `NULLS LAST`

#### Scenario: Backfill tài liệu NULL hiện có

- **WHEN** chạy migration/script backfill
- **THEN** mọi `raw_documents` có `published_at IS NULL` được set `published_at = fetched_at`

#### Scenario: Ngày ổn định khi crawl lại

- **WHEN** cùng một entry thiếu ngày được crawl lại
- **THEN** `exists_by_fingerprint` skip nó → giữ nguyên `published_at` lần đầu (không nhảy sang ngày mới)

### Requirement: Freshness gate 6 tháng tại ingestion

Hệ thống SHALL không đưa vào pipeline phân tích các tài liệu có `published_at` cũ hơn 6 tháng. Ngưỡng SHALL cấu hình được (`max_age_months`, mặc định 6) và override được per-source qua `Source.config`.

#### Scenario: Bỏ qua bài quá cũ

- **WHEN** một entry có `published_at < now() - 6 tháng`
- **THEN** hệ thống bỏ qua, KHÔNG lưu và KHÔNG gọi Gemini cho bài đó
- **AND** không phát sinh chi phí quota (chỉ so sánh ngày)

#### Scenario: Bài trong vòng 6 tháng được xử lý

- **WHEN** một entry có `published_at >= now() - 6 tháng` (bao gồm doc vừa gán ngày crawl)
- **THEN** doc được lưu và đưa vào hàng đợi phân tích bình thường

### Requirement: Ưu tiên hàng đợi tài liệu mới nhất

Hàng đợi phân tích SHALL trả tài liệu `pending` theo `published_at` giảm dần để tin mới lên trang trước và không tiêu quota vào backlog cũ.

#### Scenario: Sắp xếp newest-first

- **WHEN** gọi `get_pending()`
- **THEN** kết quả sắp theo `published_at DESC NULLS LAST`, giới hạn theo `limit`

### Requirement: Dedup giữ fingerprint bất tử

Cơ chế dedup theo `fingerprint` (SHA-256 của `source_url + title`) SHALL chặn re-crawl bất kể `processing_status`. Fingerprint SHALL không bao giờ bị xóa, kể cả sau khi tài liệu bị purge do quá hạn.

#### Scenario: Skip re-crawl mọi trạng thái

- **WHEN** một entry đã tồn tại trong `raw_documents` (dù status là `analyzed`, `low_signal`, `failed`, hay `expired`)
- **THEN** `exists_by_fingerprint` trả true → hệ thống skip, KHÔNG tạo doc mới, KHÔNG phân tích lại

### Requirement: Purge tài liệu quá hạn kiểu tombstone

Hệ thống SHALL dọn tài liệu và insight có `published_at` cũ hơn TTL (mặc định 6 tháng) bằng cách: ẩn insight (`status='expired'`), xóa content nặng (`raw_content`, `normalized_content`), đặt `raw_documents.status='expired'`, nhưng **GIỮ** `fingerprint`. Hệ thống SHALL KHÔNG hard-delete `raw_documents`.

#### Scenario: Tombstone khi quá TTL

- **WHEN** job purge chạy và gặp doc/insight có `published_at < now() - TTL`
- **THEN** insight liên quan được set `status='expired'` (xử lý trước vì FK không cascade)
- **AND** `raw_content` và `normalized_content` được set NULL để nhẹ DB
- **AND** `raw_documents.status='expired'` còn `fingerprint` được giữ nguyên

#### Scenario: Không phân tích lại sau purge

- **WHEN** một bài đã bị tombstone (kể cả bài từng đạt chuẩn) xuất hiện lại trong feed và bị crawl lại nhiều tháng sau
- **THEN** `exists_by_fingerprint` trả true → skip → KHÔNG tốn quota Gemini phân tích lại

#### Scenario: Loại tài liệu expired khỏi hàng đợi

- **WHEN** `get_pending()` chạy
- **THEN** tài liệu `status='expired'` KHÔNG được trả về (chỉ lấy `pending`)

