## 1. Dependencies

- [x] 1.1 Thêm `httpx` và `trafilatura` vào `backend/requirements.txt`
- [x] 1.2 Rebuild Docker image: `docker-compose build backend`

## 2. Web Article Connector

- [x] 2.1 Tạo `backend/app/connectors/web_article_connector.py` — trafilatura wrapper với method `extract(url, timeout)`, trả `(content, metadata)` hoặc `None`
- [x] 2.2 Test thủ công: extract article từ 3 URL khác nhau (blog, news, github) → verify output

## 3. HackerNews Connector

- [x] 3.1 Tạo `backend/app/connectors/hackernews_connector.py` — implements `BaseConnector`, gọi HN Firebase API
- [x] 3.2 Implement `fetch()`: get top stories → filter by score → extract full article via `WebArticleConnector`
- [x] 3.3 Handle edge cases: self-post (Ask HN), failed extraction, timeout
- [x] 3.4 Register vào `ConnectorRegistry` với source_type `"hackernews"`

## 4. Reddit Connector

- [x] 4.1 Tạo `backend/app/connectors/reddit_connector.py` — implements `BaseConnector`, gọi Reddit `.json` endpoint
- [x] 4.2 Implement `fetch()`: get subreddit posts → filter by upvotes → extract self-post hoặc follow link
- [x] 4.3 Thêm User-Agent header: `"AIRadarBot/1.0"`
- [x] 4.4 Register vào `ConnectorRegistry` với source_type `"reddit"`

## 5. Cost Controls

- [x] 5.1 Thêm `MIN_CONTENT_LENGTH` và `MAX_DAILY_ANALYSIS` vào `backend/app/config.py`
- [x] 5.2 Implement `min_content_length` filter trong `IngestionService` — skip bài quá ngắn
- [x] 5.3 Implement daily analysis cap trong `AnalyzerService`

## 6. Seed Sources

- [x] 6.1 Thêm HackerNews source vào `backend/app/scripts/seed_sources.py`
- [x] 6.2 Thêm Reddit sources (r/MachineLearning, r/artificial) vào seed script
- [x] 6.3 Cập nhật `connectors/__init__.py` — import HN và Reddit connector để trigger registration

## 7. Documentation

- [x] 7.1 Đọc toàn bộ `docs/system_overview.md` và cập nhật chính xác: thêm HN/Reddit/Web connector vào kiến trúc, pipeline, danh sách nguồn, dependencies

## 8. Verification

- [x] 8.1 Chạy `seed_sources` — verify HN, Reddit sources được tạo
- [x] 8.2 Chạy `run_ingestion` — verify HN connector lấy được stories + extract articles
- [x] 8.3 Chạy `run_ingestion` — verify Reddit connector lấy được posts + extract articles
- [x] 8.4 Verify `min_content_length` filter — bài ngắn bị skip
- [x] 8.5 Chạy `run_analysis` — verify insights được tạo từ HN/Reddit documents
