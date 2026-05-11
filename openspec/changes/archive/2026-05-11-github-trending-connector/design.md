## Context

Hệ thống có ConnectorRegistry pattern (`connector-framework-refactor` archived). RSSConnector, HackerNewsConnector, RedditConnector, WebArticleConnector đã implement pattern.

GitHub Trending là loại signal khác hẳn — không phải feed news/discussion, mà là metric của activity. Connector cần:
- Scrape HTML (không có RSS/API official)
- Parse repo metadata structured (stars, forks, language)
- Convert thành `ConnectorEntry` với title = repo name, raw_content = description, metadata = GitHub-specific extras

### Modules bị ảnh hưởng

- **M2 (Ingestion)**: connector mới
- **M4 (AI Analysis)**: optional context injection cho trending repos
- **M1 (Sources)**: seed sources mới với source_type="github_trending"

### Trạng thái hiện tại

- `BaseConnector` ABC + `ConnectorEntry` dataclass đã có
- `ConnectorRegistry` đã hỗ trợ register new types
- HackerNews/Reddit connector đã pattern hoá việc lấy data không qua RSS

## Goals / Non-Goals

**Goals:**
- `GitHubTrendingConnector(BaseConnector)` implement đầy đủ
- 3-4 seed sources khác nhau (all/python/weekly/topic)
- Trending data từ GitHub được biến thành insights chất lượng (signal/why_it_matters meaningful)
- Resilient: nếu HTML structure GitHub đổi, connector return empty list + log warning, không crash pipeline

**Non-Goals:**
- Không dùng GitHub REST/GraphQL API
- Không clone repo / đọc README
- Không track repo qua thời gian (mỗi lần fetch là snapshot)
- Không build frontend cho metadata GitHub-specific

## Decisions

### D1: HTML scraping — selector strategy

GitHub trending HTML structure (relatively stable since 2018):

```html
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/{owner}/{repo}">...</a>
  </h2>
  <p class="col-9 color-fg-muted">{description}</p>
  <div class="f6 color-fg-muted mt-2">
    <span itemprop="programmingLanguage">{language}</span>
    <a href=".../stargazers">{total_stars}</a>
    <a href=".../forks">{forks}</a>
    <span class="d-inline-block float-sm-right">
      {stars_today} stars today
    </span>
  </div>
</article>
```

Selectors:
- `article.Box-row` cho mỗi repo
- `h2 a` cho name + URL
- `p.color-fg-muted` cho description
- `[itemprop="programmingLanguage"]` cho language
- Parse stars_today từ text "N stars today/this week/this month"

Dùng `BeautifulSoup` (đã có trong dependencies từ normalizer).

### D2: ConnectorEntry mapping

```python
ConnectorEntry(
    source_url=f"https://github.com{href}",
    title=f"{owner}/{repo}",
    raw_content=description or "",
    author=None,  # GitHub không expose primary author từ trending page
    published_at=None,  # Trending là daily metric, không có publish time
    metadata={
        "stars_today": 245,
        "total_stars": 12500,
        "forks": 380,
        "language": "Python",
        "trend_window": "daily",  # daily | weekly | monthly
        "trending_position": 3,  # rank trong list (1-25)
    }
)
```

`metadata` field sẵn có trong ConnectorEntry (từ change `connector-framework-refactor`).

### D3: Source schema cho github_trending

```python
{
    "name": "GitHub Trending — Python Daily",
    "source_type": "github_trending",
    "feed_url": None,  # không dùng
    "trust_tier": "high",
    "topics": ["Công nghệ", "Trí tuệ nhân tạo"],
    "region": "global",
    "target_roles": ["Engineering", "Data/AI"],
    "status": "active",
    "config": {
        "language": "python",  # "" cho all
        "since": "daily",       # daily | weekly | monthly
        "max_items": 25,
    }
}
```

Connector đọc `source.config` để build URL: `https://github.com/trending/{language}?since={since}`.

### D4: Seed sources — 4 sources khác nhau

```
1. GitHub Trending — All Daily
   config: {language: "", since: "daily", max_items: 25}

2. GitHub Trending — Python Daily
   config: {language: "python", since: "daily", max_items: 25}

3. GitHub Trending — Weekly All
   config: {language: "", since: "weekly", max_items: 25}

4. GitHub Trending — TypeScript Daily
   config: {language: "typescript", since: "daily", max_items: 15}
```

Có thể thêm Go/Rust/Jupyter sau nếu thấy giá trị.

**Không** seed `language=jupyter` riêng vì GitHub không có alias `jupyter` — Jupyter notebooks lẫn vào general AI/ML repos.

### D5: Optional context injection cho analyzer

Khi `source.source_type = "github_trending"`, AnalyzerService inject thêm context vào prompt:

```
[Đây là một repository đang nổi lên trên GitHub Trending — {N} stars today, ngôn ngữ {language}. Hãy đánh giá tại sao repo này đang được chú ý và có nên test/follow không.]
```

→ Gemini sẽ generate `signal` và `recommendations` phù hợp với context "trending repo" thay vì "tin tức".

Implement trong scope này hay defer? **Defer** — chỉ làm sau khi `insight-prompt-revamp` archived và stable. Trong scope này chỉ ensure raw_documents được tạo đúng từ trending page.

### D6: Resilience & rate limiting

- Timeout 10s cho HTTP request
- User-Agent header rõ ràng (`AI Radar Impact Bot v1.0`)
- Nếu HTTP error / HTML structure đổi → log warning + return `[]` (không raise)
- Không cần rate limit vì 4 sources × 1 lần/ngày = không tải GitHub

### D7: Dedup behavior

Repos có thể trending nhiều ngày liên tiếp:
- Day 1: `pytorch/torchtune` trending
- Day 2: `pytorch/torchtune` trending lại

Fingerprint hiện tại = SHA256(source_url + title) → 2 lần fetch giống hệt = dedup, skip ngày 2.

Đây là behavior mong muốn — không muốn tạo insight trùng cho cùng repo ngày khác nhau.

Nhưng nếu repo trending lại sau 1 tháng (signal "đang nổi lên trở lại")?
- Vẫn dedup vì cùng URL+title
- Acceptable cho MVP; nếu cần track re-trending sẽ là follow-up change

### API endpoints bị ảnh hưởng

Không có. Source/insight endpoints không đổi.

### Bảng DB bị ảnh hưởng

Không thay đổi schema. Chỉ thêm 4 rows vào `sources`.

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| GitHub đổi HTML structure | Connector test selector mỗi lần parse; nếu fail → return `[]` + log; không crash pipeline. Add monitoring/alert sau (defer). |
| GitHub block/rate limit scraping | Set User-Agent rõ ràng; max 4 fetches/ngày; nếu bị block, fallback sang public mirror như `gtrending.io` (defer) |
| Repos không AI lọt vào | Analyzer trust confidence threshold 0.3 sẽ drop nếu không relevant; topics filter qua Gemini sẽ flag đúng |
| stars_today format đổi (e.g., "1.2k stars today") | Parse regex tolerate cả số nguyên và "Nk"; test edge cases |
| Trending page có thể trả 0 entries (đặc biệt language hiếm) | OK — không lỗi, chỉ skipped count |
| Ingest hàng ngày vs trending là daily/weekly/monthly | Nếu cron daily ingest cả 3 windows = duplicate cao. Recommend: daily window mỗi ngày, weekly chỉ thứ 2, monthly đầu tháng (logic này nên ở scheduler, defer cho change Teams/scheduler sau) |
