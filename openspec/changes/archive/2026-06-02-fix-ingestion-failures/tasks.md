## 1. Cập nhật các Connectors ở Backend

- [x] 1.1 Thay đổi Reddit API endpoint từ .json sang .rss và tích hợp đọc feed bằng feedparser trong reddit_connector.py
- [x] 1.2 Viết logic BeautifulSoup trong reddit_connector.py để phân biệt và bóc tách bài tự viết (self-post) với bài chia sẻ link ngoài (link-post), đồng thời loại bỏ filter min_upvotes
- [x] 1.3 Tích hợp WebArticleConnector trong rss_connector.py để cào toàn bộ bài viết từ link gốc khi cờ fetch_full_content bật trong config nguồn tin
- [x] 1.4 Thêm cơ chế fallback trong rss_connector.py để lấy tóm tắt ngắn từ XML feed khi cào bài viết gốc thất bại

## 2. Ingestion & Seeds Configuration

- [x] 2.1 Cập nhật logic lọc độ dài tối thiểu trong ingestion.py để ưu tiên lấy min_content_length từ cấu hình riêng của nguồn tin
- [x] 2.2 Thêm cấu hình min_content_length=0 cho hai nguồn GitHub Releases trong seed_sources.py
- [x] 2.3 Thêm cấu hình fetch_full_content=true cho các nguồn RSS chỉ trả về tóm tắt ngắn trong seed_sources.py

## 3. Sửa Scripts & Xác Minh (Verification)

- [x] 3.1 Sửa lỗi crash trong verify_feeds.py bằng cách lọc bỏ qua các nguồn tin không phải RSS hoặc thiếu feed_url
- [x] 3.2 Chạy script seed_sources.py để đồng bộ cấu hình nguồn tin mới vào cơ sở dữ liệu
- [x] 3.3 Chạy script verify_feeds.py để xác nhận không còn crash khi kiểm tra nguồn tin
- [x] 3.4 Thực hiện cào thử nguồn tin Reddit và xác nhận lưu thành công các tài liệu mới
- [x] 3.5 Thực hiện cào thử nguồn tin GitHub Releases và xác nhận tài liệu ngắn không bị lọc bỏ qua
- [x] 3.6 Thực hiện cào thử OpenAI Blog và kiểm tra độ dài nội dung cào được lớn hơn 2000 ký tự (đầy đủ nội dung bài gốc)
