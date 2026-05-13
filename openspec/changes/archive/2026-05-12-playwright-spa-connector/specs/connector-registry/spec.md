## ADDED Requirements

### Requirement: ConnectorRegistry hỗ trợ `playwright`
ConnectorRegistry MUST hỗ trợ thêm connector type `playwright` (cùng với `rss`, `hackernews`, `reddit`, `web_article`, `github_trending`, `huggingface`, `web_index`).

#### Scenario: Register playwright tại module load
- **WHEN** application khởi động và `app.connectors` được import
- **THEN** `ConnectorRegistry.list_registered()` chứa `"playwright"`

#### Scenario: Lookup từ IngestionService
- **WHEN** IngestionService xử lý source có `source_type="playwright"`
- **THEN** `ConnectorRegistry.get("playwright")` trả instance `PlaywrightConnector`
