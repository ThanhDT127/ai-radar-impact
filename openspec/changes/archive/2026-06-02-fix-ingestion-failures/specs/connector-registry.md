## ADDED Requirements

### Requirement: Cào các bài viết Reddit thông qua RSS feed và bóc tách link ngoài
Hệ thống phải cào các bài viết từ subreddits qua RSS feed không bị chặn 403, đồng thời phân tích HTML trong summary để bóc tách link gốc và phân biệt tin tự viết (self-post) với tin chia sẻ link ngoài (link-post).

#### Scenario: Trích xuất bài viết tự viết trên Reddit (Self-Post)
- **WHEN** Xử lý một entry từ Reddit RSS có URL thẻ `[link]` trùng với URL thẻ `[comments]` (permalink trên Reddit).
- **THEN** Hệ thống phân loại đây là self-post, trích xuất nội dung văn bản trực tiếp từ HTML summary làm `raw_content`.

#### Scenario: Trích xuất bài viết chia sẻ link ngoài trên Reddit (Link-Post)
- **WHEN** Xử lý một entry từ Reddit RSS có URL thẻ `[link]` khác với URL thẻ `[comments]` (permalink trên Reddit).
- **THEN** Hệ thống phân loại đây là link-post, sử dụng `WebArticleConnector` để tải và trích xuất nội dung toàn văn từ URL thẻ `[link]` làm `raw_content`.
