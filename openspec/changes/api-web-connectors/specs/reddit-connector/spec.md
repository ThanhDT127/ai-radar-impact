## ADDED Requirements

### Requirement: Fetch posts từ Reddit subreddit
RedditConnector lấy posts từ subreddit qua `.json` endpoint, filter theo upvotes, và follow link extract full article.

#### Scenario: Fetch subreddit posts
- **WHEN** `RedditConnector.fetch(source)` được gọi
- **THEN** gọi `GET /r/{subreddit}/.json?limit={max_items}` với User-Agent header

#### Scenario: Filter by upvotes
- **WHEN** post có `ups < source.config.min_upvotes` (default 20)
- **THEN** skip post đó

#### Scenario: Self-post content
- **WHEN** post có `is_self=true` (text post trên Reddit)
- **THEN** dùng `selftext` làm `raw_content`

#### Scenario: Link post → extract article
- **WHEN** post có URL ngoài (link post)
- **THEN** dùng `WebArticleConnector.extract(url)` để lấy full article text

#### Scenario: Reddit API rate limit
- **WHEN** gọi Reddit API
- **THEN** tuân thủ rate limit bằng `max_items` config (default 25)
