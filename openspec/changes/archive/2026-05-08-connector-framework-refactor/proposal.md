## Why

Hiện tại `IngestionService` hardcode logic `if source_type == "rss"` để chọn connector. Khi mở rộng sang API (HackerNews, Reddit) và Web scraping (trafilatura), mỗi lần thêm connector mới phải sửa trực tiếp vào `ingestion.py` — vi phạm Open/Closed Principle.

Change này refactor thành **registry-based connector pattern**: mỗi connector tự đăng ký, `IngestionService` chỉ cần query registry theo `source_type` → nhận đúng connector → gọi `fetch()`. Kiến trúc sẵn sàng cho Change 2 (api-web-connectors) mà không cần sửa lại pipeline.

## What Changes

- Tạo `BaseConnector` abstract class với interface chuẩn `fetch(source) → list[ConnectorEntry]`
- Tạo `ConnectorEntry` dataclass thay thế `FeedEntry` — generic cho mọi loại connector
- Tạo `ConnectorRegistry` — singleton map `source_type → ConnectorClass`
- Refactor `RSSConnector` implements `BaseConnector`
- Refactor `IngestionService` dùng registry thay vì if/else
- Refactor `normalizer.py` nhận `ConnectorEntry` thay vì `FeedEntry`
- Cập nhật `docs/system_overview.md` phản ánh kiến trúc mới

## Capabilities

### New Capabilities
- `connector-registry`: Registry-based connector pattern — cho phép register/lookup connector theo source_type, hỗ trợ mở rộng không cần sửa pipeline

### Modified Capabilities
- `rss-ingestion`: RSSConnector giờ implements BaseConnector interface, output ConnectorEntry thay vì FeedEntry

## Impact

- **Backend code:** `connectors/`, `services/ingestion.py`, `services/normalizer.py`
- **Database:** Không thay đổi schema
- **Frontend:** Không thay đổi
- **API:** Không thay đổi
- **Dependencies:** Không thêm dependency mới
- **Phase:** Phase 1

## Non-goals

- Không thêm connector mới (HN, Reddit) — đó là Change 2
- Không thay đổi database schema
- Không thêm scheduler hoặc API endpoints
- Không refactor frontend
