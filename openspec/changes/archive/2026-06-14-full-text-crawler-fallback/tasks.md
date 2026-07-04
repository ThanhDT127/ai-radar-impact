## 1. Playwright / CloakBrowser Integration

- [x] 1.1 Thêm thư viện `trafilatura` vào `requirements.txt` hoặc môi trường (đã có sẵn `playwright`).
- [x] 1.2 Cài đặt hàm `_fetch_full_text_with_cloak` để khởi tạo kết nối qua CDP tới `http://cloak:9222`.
- [x] 1.3 Thêm script xoá cờ `navigator.webdriver` để vượt cơ chế chống bot.
- [x] 1.4 Chờ trang tải xong (thông qua sự kiện `domcontentloaded` hoặc delay) và lấy mã nguồn HTML.
- [x] 1.5 Truyền HTML vào `trafilatura.extract()` với tuỳ chọn `include_tables=False` để bóc tách toàn bộ văn bản thuần tuý.

## 2. RSS Ingestion Fallback

- [x] 2.1 Cập nhật `rss_connector.py` để lấy đoạn văn bản hiện tại từ `feedparser`.
- [x] 2.2 Bổ sung logic kiểm tra độ dài: Nếu văn bản dưới 500 ký tự, gọi hàm fallback `_fetch_full_text_with_cloak`.
- [x] 2.3 Xử lý ngoại lệ (Try/Except) để đảm bảo nếu Playwright thất bại hoặc timeout, trình cào tin vẫn giữ lại được snippet cũ mà không crash luồng chính.
- [x] 2.4 Đảm bảo nội dung thu được (Full-text) ghi đè lên trường `content` để chuẩn bị lưu vào bảng `raw_documents`.
