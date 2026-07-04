## Context

Hệ thống AI Radar Impact hiện tại gặp 3 vấn đề lớn trong pipeline thu thập dữ liệu (Module M2 - Ingestion):
1. **Reddit API block**: `RedditConnector` sử dụng HTTP JSON API và bị Reddit trả về lỗi 403.
2. **RSS Truncated Summaries**: `RSSConnector` chỉ lấy thông tin tóm tắt có sẵn trong thẻ summary/description của XML feed. Một số nguồn tin lớn (như OpenAI Blog, Microsoft AI) chỉ cấu hình trả về 1-2 câu tóm tắt trong RSS, dẫn đến việc Gemini (M4) thiếu nội dung chi tiết để phân tích.
3. **GitHub Releases Filtered**: Feed `releases.atom` của DeepSeek và Yi trả về nội dung release notes rất ngắn, bị bộ lọc độ dài tối thiểu toàn cục (`min_content_length = 200`) của `IngestionService` (M2) loại bỏ.
4. **verify_feeds.py crash**: Script kiểm tra feed bị crash do cố parse các nguồn không có `feed_url`.

## Goals / Non-Goals

**Goals:**
- Thu thập thành công các bài viết mới từ Reddit (r/MachineLearning, r/artificial) mà không bị lỗi 403.
- Tự động cào và trích xuất nội dung toàn văn (full article content) từ trang đích cho các nguồn tin RSS bị giới hạn tóm tắt.
- Lưu trữ thành công các bản tin cực ngắn nhưng quan trọng từ GitHub Releases.
- Sửa lỗi crash trong công cụ kiểm tra `verify_feeds.py`.

**Non-Goals:**
- Không thay đổi database schema của hệ thống (các bảng `sources`, `raw_documents`, `insights`).
- Không thay đổi model AI (Gemini 2.5 Flash) hay prompt phân tích.
- Không cấu hình hệ thống proxy hay dịch vụ bypass Cloudflare phức tạp.

## Decisions

### 1. Di chuyển Reddit sang RSS Feed
- Chuyển URL đích từ JSON API sang RSS Feed (`https://www.reddit.com/r/{subreddit}/.rss`).
- Đọc feed bằng `feedparser`. Phân tích HTML trong thẻ `<summary>` của entry qua `BeautifulSoup` để xác định loại bài viết:
  - Nếu thẻ `<a href="...">[link]</a>` có URL trùng với thẻ `<a href="...">[comments]</a>` (permalink của Reddit comment page): Đây là **Self-Post**. Nội dung chính `raw_content` là text của summary.
  - Nếu khác nhau: Đây là **Link-Post**. URL của link đó chính là trang đích bên ngoài. Sử dụng `WebArticleConnector` để cào trang đích này làm `raw_content`.
- **Đánh đổi**: Bỏ qua bộ lọc `min_upvotes` cho Reddit do RSS không trả về số lượng upvotes.

### 2. Tích hợp cào bài viết gốc cho RSS Connector
- Thêm cờ cấu hình `"fetch_full_content": true` trong `Source.config`.
- Khi cờ này bật, `RSSConnector` sẽ gọi `WebArticleConnector().extract(entry.link)` để tải và trích xuất nội dung chi tiết từ URL trang nguồn.
- Ghi đè `raw_content` và `author` bằng kết quả cào được. Fallback về tóm tắt ngắn từ RSS feed nếu cào lỗi.

### 3. Ghi đè cấu hình `min_content_length` theo nguồn tin
- Cập nhật `IngestionService` để đọc `min_content_length` từ `source.config.get("min_content_length")` trước, nếu không có mới lấy cấu hình mặc định toàn cục `settings.min_content_length`.
- Bổ sung cấu hình `"min_content_length": 0` cho các nguồn GitHub Releases.

### 4. Khắc phục lỗi `verify_feeds.py`
- Lọc danh sách `INITIAL_SOURCES`, chỉ parse các nguồn có `source_type == "rss"` và `feed_url` không phải `None`.

---

## Risks / Trade-offs

- **Tốc độ cào (Fetch latency)**: Việc cào toàn bộ nội dung qua `WebArticleConnector` (trafilatura) cho các nguồn RSS sẽ phát sinh thêm các HTTP requests đồng bộ trong tiến trình cào. Tuy nhiên, do giới hạn `max_items` (10-15 bài) và tần suất chạy cron job, việc này không gây quá tải và là sự đánh đổi xứng đáng để có dữ liệu phân tích đầy đủ cho Gemini.
- **Rủi ro Rate Limit**: Một số trang web có thể chặn trafilatura cào bài viết gốc. Do đó, cơ chế fallback về tóm tắt ngắn của RSS feed khi cào lỗi là bắt buộc để đảm bảo hệ thống luôn có dữ liệu tối thiểu.
