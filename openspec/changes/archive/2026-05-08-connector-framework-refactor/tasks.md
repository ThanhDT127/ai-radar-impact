## 1. Base Classes

- [x] 1.1 Tạo `backend/app/connectors/base.py` — định nghĩa `ConnectorEntry` dataclass và `BaseConnector` abstract class
- [x] 1.2 Tạo `backend/app/connectors/registry.py` — `ConnectorRegistry` class với methods `register()`, `get()`, `list_registered()`

## 2. Refactor RSSConnector

- [x] 2.1 Refactor `backend/app/connectors/rss_connector.py` — kế thừa `BaseConnector`, method `fetch()` trả `list[ConnectorEntry]` thay vì `list[FeedEntry]`
- [x] 2.2 Xóa class `FeedEntry` khỏi `rss_connector.py` (đã được thay bằng `ConnectorEntry`)
- [x] 2.3 Thêm auto-registration: `ConnectorRegistry.register("rss", RSSConnector)` cuối module

## 3. Refactor Normalizer

- [x] 3.1 Cập nhật `backend/app/services/normalizer.py` — import `ConnectorEntry` thay vì `FeedEntry`, cập nhật type hints
- [x] 3.2 Verify `normalize_entry()` hoạt động đúng với `ConnectorEntry`

## 4. Refactor IngestionService

- [x] 4.1 Cập nhật `backend/app/services/ingestion.py` — xóa import `RSSConnector` trực tiếp, dùng `ConnectorRegistry.get(source.source_type)`
- [x] 4.2 Xóa logic `if source_type == "rss"` — thay bằng registry lookup
- [x] 4.3 Handle `ValueError` khi source_type chưa được đăng ký — log warning và skip

## 5. Module Init

- [x] 5.1 Cập nhật `backend/app/connectors/__init__.py` — import `RSSConnector` để trigger auto-registration, export `ConnectorRegistry`, `BaseConnector`, `ConnectorEntry`

## 6. Documentation

- [x] 6.1 Đọc toàn bộ `docs/system_overview.md` và cập nhật chính xác: Section 2 (kiến trúc tổng quan), Section 3.1 (lấy dữ liệu), Section 6 (giới hạn) — phản ánh connector registry pattern

## 7. Verification

- [x] 7.1 Chạy `docker-compose up -d` — hệ thống khởi động bình thường
- [x] 7.2 Chạy `run_ingestion` — RSS ingestion hoạt động đúng với connector mới
- [x] 7.3 Verify kết quả `raw_documents` — fingerprint và normalized_content giống hệt trước refactor
