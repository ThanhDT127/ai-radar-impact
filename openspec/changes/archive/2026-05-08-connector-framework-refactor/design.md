## Context

Hệ thống hiện tại dùng `RSSConnector` duy nhất, gọi trực tiếp trong `IngestionService` qua logic `if source_type == "rss"`. Khi cần mở rộng sang HackerNews API, Reddit API, Web article extraction (Change 2), mô hình này không scale được — mỗi connector mới yêu cầu sửa trực tiếp `ingestion.py`.

Change này chuyển sang **registry pattern**: connector tự đăng ký vào registry theo `source_type`, `IngestionService` chỉ cần lookup registry để lấy đúng connector.

### Modules bị ảnh hưởng
- **M2 (Ingestion):** Refactor pipeline core — dùng registry thay vì hardcode
- **M3 (Normalization):** `normalizer.py` nhận `ConnectorEntry` thay vì `FeedEntry`

### Trạng thái hiện tại
- `backend/app/connectors/rss_connector.py` — standalone class, trả `FeedEntry`
- `backend/app/services/ingestion.py` — hardcode `if source_type == "rss"`
- `backend/app/services/normalizer.py` — import `FeedEntry` trực tiếp

## Goals / Non-Goals

**Goals:**
- Tạo `BaseConnector` abstract class với interface chuẩn `fetch(source) → list[ConnectorEntry]`
- Tạo `ConnectorEntry` dataclass generic thay thế `FeedEntry`
- Tạo `ConnectorRegistry` singleton quản lý mapping `source_type → ConnectorClass`
- Refactor `RSSConnector` implements `BaseConnector`
- Refactor `IngestionService` dùng registry — xóa bỏ if/else
- Refactor `normalizer.py` nhận `ConnectorEntry`
- Cập nhật `docs/system_overview.md` phản ánh kiến trúc mới

**Non-Goals:**
- Không thêm connector mới (HN, Reddit, Web) — đó là Change 2
- Không thay đổi database schema
- Không thay đổi API endpoints
- Không thay đổi frontend

## Decisions

### D1: ConnectorEntry thay thế FeedEntry
`ConnectorEntry` là dataclass generic hơn `FeedEntry`:

```python
@dataclass
class ConnectorEntry:
    source_url: str
    title: str
    raw_content: str
    author: str | None = None
    published_at: datetime | None = None
    metadata: dict = field(default_factory=dict)  # connector-specific data
```

Field `metadata` cho phép connector-specific data (ví dụ: HN score, Reddit upvotes) mà không cần thay đổi schema.

### D2: BaseConnector abstract class

```python
class BaseConnector(ABC):
    @abstractmethod
    def fetch(self, source: Source) -> list[ConnectorEntry]:
        """Fetch entries from the source. Returns list of ConnectorEntry."""
        ...
```

Mỗi connector implements method `fetch()` duy nhất. Đơn giản, dễ test.

### D3: ConnectorRegistry — simple dict mapping

```python
class ConnectorRegistry:
    _connectors: dict[str, type[BaseConnector]] = {}

    @classmethod
    def register(cls, source_type: str, connector_class: type[BaseConnector]):
        cls._connectors[source_type] = connector_class

    @classmethod
    def get(cls, source_type: str) -> BaseConnector:
        cls_type = cls._connectors.get(source_type)
        if not cls_type:
            raise ValueError(f"No connector registered for type: {source_type}")
        return cls_type()
```

Registry dùng class-level dict, register tại module load time. Không cần DI framework phức tạp.

### D4: Auto-registration via module import
`connectors/__init__.py` import tất cả connector modules → trigger registration:

```python
# connectors/__init__.py
from app.connectors.rss_connector import RSSConnector  # triggers register
```

### D5: Cập nhật system_overview.md
Đọc toàn bộ `docs/system_overview.md`, cập nhật:
- Section 2 (Kiến trúc): thêm Connector Registry vào diagram
- Section 3.1 (Lấy dữ liệu): mô tả registry-based flow
- Section 6 (Giới hạn): cập nhật "chưa có nhiều connector ngoài RSS" → "đã có connector framework"

### API endpoints bị ảnh hưởng
Không có. Change này chỉ refactor internal code.

### Bảng DB bị ảnh hưởng
Không có. Không thay đổi schema.

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| Registry pattern thêm một lớp abstraction | Giữ registry đơn giản — chỉ là dict mapping, không over-engineer |
| `FeedEntry` → `ConnectorEntry` rename có thể gây lỗi import ở nhiều nơi | Grep toàn bộ `FeedEntry` references trước khi đổi, update tất cả |
| Backward compatibility — RSS ingestion phải hoạt động y hệt sau refactor | Test thủ công: chạy ingestion trước và sau refactor, so sánh kết quả |
