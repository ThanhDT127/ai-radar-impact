## Why

Hiện tại, hệ thống AI Radar Impact đang bị lỗi không thu thập được bài viết từ một số nguồn tin quan trọng:
1. **Reddit (`r/MachineLearning`, `r/artificial`)**: API JSON (`.json`) bị chặn lỗi 403 do chính sách chống bot của Reddit.
2. **GitHub Releases**: Atom feed trả về bài viết rất ngắn nên bị bộ lọc độ dài tối thiểu toàn cục (`min_content_length = 200` ký tự) lọc bỏ qua.
3. **Các nguồn tin RSS khác**: Nhiều trang tin (như OpenAI Blog, Google DeepMind) chỉ trả về tóm tắt ngắn trong XML feed, dẫn đến việc Gemini chỉ phân tích được 1-2 câu mở đầu thay vì toàn bộ bài viết chi tiết gốc.
4. ** verify_feeds.py**: Crash khi cố parse các nguồn không phải RSS (không có `feed_url`).

## What Changes

1. **Reddit Connector**: Di chuyển từ gọi API JSON sang đọc RSS Feed (`.rss`) qua `feedparser`, phân tích HTML summary để bóc tách bài tự viết (self-post) và bài chia sẻ link ngoài (link-post).
2. **RSS Full Content Extraction**: Tích hợp cào tự động và trích xuất nội dung toàn bộ bài viết từ link gốc (sử dụng `WebArticleConnector` có sẵn) đối với các nguồn RSS được cấu hình `"fetch_full_content": true`.
3. **Bypass min_content_length**: Cho phép cấu hình ghi đè `min_content_length` cho từng nguồn tin để tránh bỏ sót các bản tin cực ngắn nhưng quan trọng (như GitHub Releases).
4. **Cấu hình & Script kiểm tra**: Cập nhật file seed nguồn tin và sửa lỗi crash của script `verify_feeds.py`.

## Capabilities

### New Capabilities
- `rss-full-content-extraction`: Tự động cào và trích xuất nội dung toàn văn từ trang đích đối với các nguồn RSS chỉ cung cấp tóm tắt ngắn.

### Modified Capabilities
- `rss-ingestion`: Thay đổi yêu cầu lưu trữ và xử lý độ dài nội dung để hỗ trợ cấu hình độ dài tối thiểu theo từng nguồn.
- `connector-registry`: Thay đổi cơ chế cào của Reddit connector sang RSS và bổ sung phân tích cấu trúc HTML summary.

## Impact

- **Phase áp dụng**: Phase 1 (MVP).
- **Dependency**: Module M2 (Ingestion) và M3 (Normalization). Không yêu cầu thay đổi database schema của các bảng chính (`sources`, `raw_documents`).
- **Non-goals**:
  - Không thay đổi logic phân tích AI của Gemini (M4).
  - Không xây dựng UI quản lý cấu hình nguồn tin mới (cấu hình qua database và file seed).
  - Không vượt tường lửa/Cloudflare bằng proxy cho Reddit JSON API.
