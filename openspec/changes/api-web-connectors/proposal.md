## Why

Sau Change 1 (connector-framework-refactor), hệ thống đã có registry pattern sẵn sàng cho connector mới. Hiện tại chỉ có 1 loại connector (RSS) — giới hạn nguồn dữ liệu vào các blog/feed có RSS.

Change này mở rộng sang 3 loại connector mới:
- **HackerNews API** — lấy top stories từ HN Firebase API, follow link bài gốc để extract full article
- **Reddit API** — lấy posts từ subreddit `.json` endpoint, follow link bài gốc
- **Web Article Extractor** — dùng `trafilatura` để extract nội dung chính từ bất kỳ URL nào

Mục tiêu: mở rộng phạm vi thu thập tin tức, đặc biệt từ community sources (Tier C) và blog links.

## What Changes

- Tạo `HackerNewsConnector` — dùng httpx async gọi HN Firebase API (`/v0/topstories.json`)
- Tạo `RedditConnector` — dùng httpx async gọi Reddit `.json` endpoint (no API key)
- Tạo `WebArticleConnector` — dùng `trafilatura` để extract full article từ URL
- HN/Reddit connector tích hợp `WebArticleConnector` để follow link → extract full content
- Thêm `httpx` và `trafilatura` vào dependencies
- Seed thêm sources cho HN, Reddit
- Config: `min_content_length`, `max_daily_analysis` cost controls
- Cập nhật `docs/system_overview.md`

## Capabilities

### New Capabilities
- `hackernews-connector`: Connector lấy top stories từ HackerNews, follow link extract full article
- `reddit-connector`: Connector lấy posts từ subreddit, follow link extract full article
- `web-article-extraction`: Dùng trafilatura extract nội dung chính từ web pages

### Modified Capabilities
- `connector-registry`: Register thêm 3 connector mới (hackernews, reddit, web)

## Impact

- **Backend code:** `connectors/`, `services/`, `scripts/seed_sources.py`, `config.py`
- **Database:** Không thay đổi schema — chỉ thêm records vào bảng `sources`
- **Frontend:** Không thay đổi
- **API:** Không thay đổi
- **Dependencies:** Thêm `httpx`, `trafilatura`
- **Dependency:** Cần Change 1 (connector-framework-refactor) hoàn thành
- **Phase:** Phase 1

## Non-goals

- Không cài Crawl4AI — dùng trafilatura là đủ
- Không thêm scheduler — vẫn chạy ingestion thủ công
- Không thêm API endpoints — dùng script hiện có
- Không implement dedup cross-source — đó là Change 3
