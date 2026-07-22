## ADDED Requirements

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

## MODIFIED Requirements

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
