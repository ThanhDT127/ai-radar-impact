## ADDED Requirements

### Requirement: Fetch top stories từ HackerNews
HackerNewsConnector lấy top stories từ HN Firebase API, filter theo score, và follow link extract full article.

#### Scenario: Fetch top stories
- **WHEN** `HackerNewsConnector.fetch(source)` được gọi
- **THEN** gọi HN API `/v0/topstories.json`, lấy top N items (theo `source.config.max_items`)

#### Scenario: Filter by score
- **WHEN** story có `score < source.config.min_score` (default 50)
- **THEN** skip story đó

#### Scenario: Extract full article
- **WHEN** story có URL bài viết gốc
- **THEN** dùng `WebArticleConnector.extract(url)` để lấy full article text
- **THEN** `raw_content` = full article text (không phải HN title/comment)

#### Scenario: HN self-post (Ask HN, Show HN)
- **WHEN** story không có URL ngoài (chỉ có text nội bộ HN)
- **THEN** dùng story text làm `raw_content`

#### Scenario: Article extraction failed
- **WHEN** `WebArticleConnector.extract(url)` trả None hoặc timeout
- **THEN** skip story, log warning
