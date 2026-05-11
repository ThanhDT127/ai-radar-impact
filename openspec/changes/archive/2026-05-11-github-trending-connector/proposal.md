## Why

Hiện tại radar bắt được tin tức (RSS) và discussion (HN/Reddit), nhưng thiếu một loại signal **rất khác và rất quý**: cộng đồng đang **build** cái gì. GitHub Trending là barometer trực tiếp về repos đang nổi lên — không phụ thuộc tin tức/PR/discussion mà reflect actual code activity.

Đây là loại signal duy nhất cho thấy "tool/library X đang được hàng nghìn người star" trước khi nó được TechCrunch viết. Đặc biệt giá trị cho radar AI vì rất nhiều innovation diễn ra ở repos cá nhân/lab nhỏ trước khi vào mainstream.

## What Changes

Tạo connector mới **`GitHubTrendingConnector`**:

- Source type mới: `"github_trending"`
- Fetch HTML từ `https://github.com/trending/{language}?since={daily|weekly|monthly}` (không có official API, scrape HTML — stable selector)
- Parse repo metadata: `name`, `url`, `description`, `language`, `stars_today`, `total_stars`, `forks`, `built_by` (top contributors)
- Trả về `ConnectorEntry` với `metadata` field chứa các thông tin GitHub-specific
- Auto-register vào `ConnectorRegistry` (kế thừa pattern đã có)

**Seed sources đa dạng**:
- `GitHub Trending — All Daily` (`language=""`)
- `GitHub Trending — Python Daily` (`language=python`)
- `GitHub Trending — Weekly Top` (`since=weekly`, language all)
- `GitHub Trending — Topic: ai` (cần evaluate URL — `/topics/{topic}` redirect, có thể không phải trending)

**Filter trong analyzer**:
- Pre-filter: chỉ pass repos có description chứa keywords liên quan AI/dev (avoid game/spam repos lọt vào AI radar)
- Hoặc dùng topics trên repo (nếu HTML có expose) để match closed taxonomy

## Capabilities

### New Capabilities
- `github-trending-ingestion`: Connector đặc thù cho GitHub Trending, fetch HTML scrape, output ConnectorEntry với metadata phong phú

### Modified Capabilities
- `connector-registry`: Đăng ký thêm `"github_trending"` source type
- `rss-ingestion` (gián tiếp): Source model dùng được cho non-RSS connector — verify `feed_url` có thể null cho `github_trending` (giống `hackernews`, `reddit`)

## Impact

- **Backend code**: 
  - Mới: `connectors/github_trending_connector.py`
  - Cập nhật: `connectors/__init__.py` (register), `scripts/seed_sources.py` (seed 3-4 sources)
  - Optional: `services/analyzer.py` thêm context "đây là repo trending" vào prompt
- **Database**: Không thay đổi schema (Source model + ConnectorRegistry pattern đã hỗ trợ)
- **Frontend**: Không bắt buộc đổi; có thể thêm metadata stars/forks vào InsightDetail nếu source_type = github_trending (defer)
- **Dependencies**: Có thể cần `beautifulsoup4` (đã có) để parse HTML
- **Phase**: Phase 2

## Non-goals

- Không dùng GitHub REST API (yêu cầu auth + rate limit; HTML trending không cần)
- Không track release history của từng repo (chỉ trending list)
- Không clone code hay đọc README sâu (chỉ description từ trending page)
- Không dedup repos cross-day (1 repo có thể trending nhiều ngày — vẫn fingerprint theo URL+title nên dedup engine xử lý)
- Không sửa frontend trong scope này

## Lưu ý quan trọng

- HTML selector của GitHub có thể thay đổi → connector phải có fallback graceful (log error, return empty list, không crash pipeline). Tương tự RSSConnector handle bozo feeds.
- Trending page **không có official API** — đây là design intentional, GitHub không khuyến khích scrape nhưng cũng không block. Nếu sau này họ chặn, fallback sang `github.com/trending` qua proxy hoặc 3rd party mirror.
- Repos không phải đều liên quan AI — cần filter ở pre-analyze hoặc tin tưởng analyzer drop confidence thấp
- `signal` từ change 1 (`insight-prompt-revamp`) đặc biệt valuable cho trending repos: "Repo X đang trending vì..." — Gemini cần context "đây là repo trending" để generate đúng signal. Có thể inject context này vào prompt khi `source_type = "github_trending"`.
