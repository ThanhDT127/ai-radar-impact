## Context

Sau Change 1, hệ thống có `ConnectorRegistry` + `BaseConnector` pattern. Change này thêm 3 connector mới vào registry.

### Modules bị ảnh hưởng
- **M2 (Ingestion):** Thêm 3 connector mới — HN, Reddit, Web Article
- **M1 (Source Management):** Seed thêm sources mới
- **M3 (Normalization):** Xử lý content từ trafilatura output

### Nguồn dữ liệu mới

| Nguồn | API Endpoint | Source Type | Trust Tier |
|:---|:---|:---|:---|
| HackerNews | `https://hacker-news.firebaseio.com/v0/` | `hackernews` | medium (Tier C) |
| Reddit r/MachineLearning | `https://www.reddit.com/r/MachineLearning/.json` | `reddit` | medium (Tier C) |
| Reddit r/artificial | `https://www.reddit.com/r/artificial/.json` | `reddit` | medium (Tier C) |

## Goals / Non-Goals

**Goals:**
- `HackerNewsConnector` — gọi HN API lấy top stories, follow link extract full article via trafilatura
- `RedditConnector` — gọi Reddit `.json` endpoint, follow link extract full article via trafilatura
- `WebArticleConnector` — standalone trafilatura wrapper, reusable cho HN/Reddit connector
- Cost controls: `min_content_length` filter (skip bài quá ngắn), `MAX_DAILY_ANALYSIS` cap
- Seed sources mới
- Cập nhật `docs/system_overview.md`

**Non-Goals:**
- Không dùng Crawl4AI
- Không dùng Reddit OAuth API (dùng `.json` endpoint, no API key)
- Không thay đổi database schema
- Không thêm API endpoints

## Decisions

### D1: HackerNews Connector flow
```
1. GET /v0/topstories.json → list[int] (story IDs)
2. GET /v0/item/{id}.json → {title, url, score, ...}
3. Filter: score >= config.min_score (default 50)
4. WebArticleConnector.extract(url) → full article text
5. Return ConnectorEntry(source_url=url, title=title, raw_content=article, metadata={hn_score: score})
```

Config trong `source.config`:
```json
{
  "max_items": 15,
  "min_score": 50,
  "fetch_timeout": 10
}
```

### D2: Reddit Connector flow
```
1. GET /r/{subreddit}/.json?limit=25 → {data: {children: [...]}}
2. Filter: ups >= config.min_upvotes (default 20)
3. Nếu post có is_self=true → dùng selftext
4. Nếu post có URL → WebArticleConnector.extract(url)
5. Return ConnectorEntry(source_url=permalink, title=title, raw_content=content, metadata={upvotes, subreddit})
```

Headers: `User-Agent: AIRadarBot/1.0` (Reddit yêu cầu UA rõ ràng).

### D3: WebArticleConnector — trafilatura wrapper
```python
class WebArticleConnector:
    def extract(self, url: str, timeout: int = 10) -> str | None:
        """Extract main article content from URL using trafilatura."""
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        return trafilatura.extract(downloaded, output_format="txt", include_comments=False)
```

Không phải `BaseConnector` — đây là utility class, được HN/Reddit connector gọi nội bộ.

### D4: Cost controls
- `min_content_length = 200` — skip bài có normalized_content < 200 chars (không đủ chất lượng cho AI analysis)
- `MAX_DAILY_ANALYSIS = 500` — giới hạn số documents được phân tích mỗi ngày
- Config trong `app/config.py`, có thể override qua env vars

### API endpoints bị ảnh hưởng
Không có.

### Bảng DB bị ảnh hưởng
Không thay đổi schema. Chỉ thêm rows vào bảng `sources`.

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| Reddit rate limit (`.json` endpoint, no API key) — khoảng 60 req/min | `max_items` config giới hạn 25, chỉ chạy manual nên không burst |
| HN article extraction timeout (trang chậm/blocked) | `fetch_timeout` config + try/except, skip failed URLs |
| trafilatura trả content rỗng cho SPA sites | Accept — SPA sites là edge case, skip và log |
| Content quá ngắn → insight kém chất lượng | `min_content_length` filter trước khi gọi AI |
