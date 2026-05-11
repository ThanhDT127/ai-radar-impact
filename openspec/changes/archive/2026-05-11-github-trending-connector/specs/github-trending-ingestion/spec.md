## ADDED Requirements

### Requirement: GitHubTrendingConnector implements BaseConnector

`GitHubTrendingConnector` MUST kế thừa `BaseConnector` và scrape `github.com/trending` để trả về danh sách repos.

#### Scenario: Fetch trending repos thành công
- **WHEN** `GitHubTrendingConnector.fetch(source)` được gọi với `source.config = {language: "python", since: "daily", max_items: 25}`
- **THEN** connector gọi `GET https://github.com/trending/python?since=daily`
- **THEN** parse HTML và trả về list `ConnectorEntry` (tối đa `max_items`)
- **THEN** mỗi entry có `title = "{owner}/{repo}"`, `source_url = "https://github.com/{owner}/{repo}"`, `raw_content = description`

#### Scenario: Metadata phong phú
- **WHEN** parse 1 trending repo
- **THEN** `ConnectorEntry.metadata` chứa: `stars_today`, `total_stars`, `forks`, `language`, `trend_window` (`daily|weekly|monthly`), `trending_position`

#### Scenario: HTML structure đổi
- **WHEN** GitHub trending HTML đổi structure → selector không match
- **THEN** connector log warning "GitHub Trending HTML parse failed for {url}"
- **THEN** return `[]` (không raise exception, không crash pipeline)

#### Scenario: HTTP error
- **WHEN** GitHub trả 5xx hoặc timeout
- **THEN** log error với URL + status
- **THEN** return `[]`

#### Scenario: Auto-registration
- **WHEN** module `github_trending_connector` được import
- **THEN** `ConnectorRegistry.register("github_trending", GitHubTrendingConnector)` được gọi
- **THEN** `IngestionService` có thể lookup connector bằng `source_type="github_trending"`

### Requirement: Source schema cho github_trending

Source với `source_type="github_trending"` MUST có `feed_url=None` và `config` chứa `language`, `since`, `max_items`.

#### Scenario: Source feed_url null
- **WHEN** seed source với `source_type="github_trending"`
- **THEN** `feed_url = None` được chấp nhận
- **THEN** `config` chứa `language`, `since`, `max_items`

#### Scenario: Config defaults
- **WHEN** source thiếu key trong config
- **THEN** connector dùng default: `language=""` (all), `since="daily"`, `max_items=25`

### Requirement: Seed sources GitHub Trending mặc định

`seed_sources` MUST tạo 4 sources `github_trending` mặc định.

#### Scenario: 4 trending sources được seed
- **WHEN** chạy `seed_sources`
- **THEN** tạo (hoặc skip):
  - `GitHub Trending — All Daily` (language="")
  - `GitHub Trending — Python Daily` (language="python")
  - `GitHub Trending — Weekly All` (since="weekly")
  - `GitHub Trending — TypeScript Daily` (language="typescript")
- **THEN** tất cả `region="global"`, `target_roles ⊇ {Engineering, Data/AI}`
