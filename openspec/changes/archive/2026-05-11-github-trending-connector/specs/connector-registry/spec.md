## ADDED Requirements

### Requirement: ConnectorRegistry hỗ trợ thêm `github_trending`

ConnectorRegistry MUST hỗ trợ thêm connector type `github_trending` (cùng với `rss`, `hackernews`, `reddit`, `web_article`).

#### Scenario: Register github_trending tại module load
- **WHEN** application khởi động và `app.connectors` được import
- **THEN** `ConnectorRegistry.list_registered()` chứa `"github_trending"` (cùng với "rss", "hackernews", "reddit", "web_article")

#### Scenario: Lookup từ IngestionService
- **WHEN** IngestionService xử lý source có `source_type="github_trending"`
- **THEN** `ConnectorRegistry.get("github_trending")` trả instance `GitHubTrendingConnector`
