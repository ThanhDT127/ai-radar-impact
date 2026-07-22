# github-trending-ingestion Specification

## Purpose
TBD - created by archiving change github-trending-connector. Update Purpose after archive.
## Requirements
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

`seed_sources` MUST tạo các sources `github_trending` mặc định, bao gồm cả khung `monthly`.

#### Scenario: Các trending sources được seed
- **WHEN** chạy `seed_sources`
- **THEN** tạo (hoặc skip nếu đã có):
  - `GitHub Trending — All Daily` (language="", since="daily")
  - `GitHub Trending — Python Daily` (language="python", since="daily")
  - `GitHub Trending — Weekly All` (since="weekly")
  - `GitHub Trending — Monthly All` (since="monthly")
  - `GitHub Trending — TypeScript Daily` (language="typescript", since="daily")
- **THEN** tất cả `region="global"`, `target_roles ⊇ {Engineering, Data/AI}`

#### Scenario: Monthly window fetch đúng
- **WHEN** ingest source `GitHub Trending — Monthly All`
- **THEN** connector gọi `GET https://github.com/trending?since=monthly`
- **THEN** metadata mỗi entry có `trend_window="monthly"`

### Requirement: Làm giàu content bằng README repo

`GitHubTrendingConnector` MUST đọc README của mỗi repo trending (qua `raw.githubusercontent.com`) và ghép vào `raw_content`, có cắt theo ngân sách ký tự, để analyzer có đủ ngữ cảnh phân tích. Việc đọc README MUST fail-safe: lỗi không được làm hỏng entry hay crash pipeline.

#### Scenario: Đọc README thành công
- **WHEN** connector parse 1 repo `{owner}/{repo}` với `config.fetch_readme=True`
- **THEN** connector GET `https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md` (thử lần lượt `README.md`, `README.markdown`, `README.rst`, `readme.md`)
- **THEN** nội dung README được cắt tối đa `readme_max_chars` (mặc định 4000) và ghép vào `raw_content` **sau** khối metadata (tên/mô tả/số sao)

#### Scenario: Repo không có README hoặc fetch lỗi
- **WHEN** tất cả filename README trả 404, hoặc request timeout/5xx
- **THEN** connector log ở mức debug, giữ nguyên `raw_content` mô tả cũ
- **THEN** entry vẫn hợp lệ và được trả về (không raise exception, không crash pipeline)

#### Scenario: Tắt đọc README theo source
- **WHEN** `source.config.fetch_readme = False`
- **THEN** connector KHÔNG fetch README
- **THEN** `raw_content` chỉ chứa metadata mô tả như trước

#### Scenario: README không vượt giới hạn prompt
- **WHEN** README dài hơn `readme_max_chars`
- **THEN** phần README trong `raw_content` bị cắt về đúng ngưỡng
- **THEN** khối metadata cốt lõi luôn nằm trước README để không bị prompt cắt mất (giới hạn 6000 ký tự)

### Requirement: Dedup theo owner/repo xuyên cửa sổ trend

Một repo trending đồng thời ở nhiều cửa sổ (`daily`/`weekly`/`monthly`) MUST chỉ tạo **1** raw document, để không phân tích lại gây tốn quota. README MUST KHÔNG được đưa vào fingerprint.

#### Scenario: Cùng repo, khác cửa sổ trend
- **WHEN** repo `{owner}/{repo}` xuất hiện ở source `since="daily"` và source `since="weekly"`
- **THEN** `make_fingerprint(source_url, title)` của hai entry BẰNG NHAU (vì `source_url` và `title` độc lập với `since`)
- **THEN** raw document thứ hai bị skip qua `exists_by_fingerprint` (chỉ còn 1 raw document cho repo đó)

#### Scenario: README thay đổi không sinh bản trùng
- **WHEN** content của repo thay đổi vì README được ghép thêm
- **THEN** fingerprint KHÔNG đổi (chỉ tính trên `source_url` + `title`)

