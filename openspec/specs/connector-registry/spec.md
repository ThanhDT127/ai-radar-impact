## Purpose

ConnectorRegistry là pattern cho phép `IngestionService` lookup connector phù hợp theo `source_type` (rss, hackernews, reddit, web_article, github_trending). Mỗi connector tự đăng ký vào registry khi module được import — không cần sửa IngestionService khi thêm connector mới.
## Requirements
### Requirement: BaseConnector interface
Mọi connector trong hệ thống MUST implement `BaseConnector` abstract class với method `fetch(source: Source) → list[ConnectorEntry]`.

#### Scenario: Connector implementation
- **WHEN** một connector mới được tạo
- **THEN** nó phải kế thừa `BaseConnector` và implement method `fetch()`

#### Scenario: ConnectorEntry output
- **WHEN** connector `fetch()` được gọi
- **THEN** trả về list `ConnectorEntry` với các field: `source_url`, `title`, `raw_content`, `author` (optional), `published_at` (optional), `metadata` (dict, optional)

### Requirement: ConnectorRegistry
Hệ thống MUST có một `ConnectorRegistry` quản lý mapping giữa `source_type` và `ConnectorClass`.

#### Scenario: Register connector
- **WHEN** module connector được import
- **THEN** connector tự đăng ký vào registry với `source_type` tương ứng

#### Scenario: Lookup connector
- **WHEN** `IngestionService` cần connector cho `source_type`
- **THEN** gọi `ConnectorRegistry.get(source_type)` → nhận instance connector đúng loại

#### Scenario: Unknown source type
- **WHEN** `ConnectorRegistry.get()` nhận `source_type` chưa đăng ký
- **THEN** raise `ValueError` với message rõ ràng

### Requirement: IngestionService dùng registry
`IngestionService` MUST không hardcode if/else cho từng `source_type`, mà dùng `ConnectorRegistry` để lookup connector dynamically.

#### Scenario: Ingestion flow
- **WHEN** `IngestionService.run()` xử lý một source
- **THEN** gọi `ConnectorRegistry.get(source.source_type)` → `connector.fetch(source)` → normalize → store

#### Scenario: Unsupported source type
- **WHEN** source có `source_type` không có connector nào đăng ký
- **THEN** log warning và skip source đó, không crash toàn bộ ingestion

### Requirement: ConnectorRegistry hỗ trợ thêm `github_trending`

ConnectorRegistry MUST hỗ trợ thêm connector type `github_trending` (cùng với `rss`, `hackernews`, `reddit`, `web_article`).

#### Scenario: Register github_trending tại module load
- **WHEN** application khởi động và `app.connectors` được import
- **THEN** `ConnectorRegistry.list_registered()` chứa `"github_trending"` (cùng với "rss", "hackernews", "reddit", "web_article")

#### Scenario: Lookup từ IngestionService
- **WHEN** IngestionService xử lý source có `source_type="github_trending"`
- **THEN** `ConnectorRegistry.get("github_trending")` trả instance `GitHubTrendingConnector`

