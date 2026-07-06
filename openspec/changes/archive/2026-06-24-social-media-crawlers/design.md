## Context

Các mạng xã hội chuyên gia (LinkedIn, X/Twitter, HackerNews, Reddit) là nguồn cung cấp tín hiệu sớm quý giá (như thay đổi policy, release model mới, cảnh báo CVE). Tuy nhiên, các nền tảng này sử dụng cơ chế bảo vệ nghiêm ngặt:
- Yêu cầu đăng nhập hoặc chặn nếu không có Cookies hợp lệ.
- Sử dụng Infinite Scroll để tải dữ liệu động (không có link trực tiếp trong DOM ngay từ đầu).
- Cơ chế Rate-limiting/Bot blocking (như cờ `navigator.webdriver`).

Để khắc phục, chúng ta đã tích hợp Playwright kết nối với CloakBrowser nhưng vẫn cần nâng cấp kỹ thuật thu thập để lấy được dạng "Feed Cards" (bài đăng trên dòng thời gian) thay vì chỉ click link bài báo truyền thống.

## Goals / Non-Goals

**Goals:**
- Nâng cấp `PlaywrightConnector` (M2: Ingestion) để hỗ trợ chế độ đọc Feed (Timeline) của mạng xã hội.
- Mô phỏng hành vi cuộn trang của người dùng (Scroll) để lấy bài viết cũ.
- Tích hợp tính năng inject cookies (`cookie_file`) để vượt qua bức tường đăng nhập của LinkedIn/X một cách an toàn.
- Hỗ trợ lưu content bài post dưới dạng văn bản (RawDocument) và sinh ra một Hash ID giả làm `source_url` do các bài đăng Feed không phải lúc nào cũng có direct URL.

**Non-Goals:**
- Không viết thuật toán auto-login (tự nhập username/password). Việc cung cấp Cookies do Admin làm thủ công.
- Không cào toàn bộ mạng xã hội, chỉ cào các `Source` đã được whitelist trong DB.
- Không sử dụng LLM hay pgvector ở phase này (M2 độc lập với M4/M8).

## Decisions

1. **Chế độ `extract_from_feed`**: 
   Thêm cờ cấu hình này vào `Source.config`. Nếu bằng `true`, Playwright sẽ không tìm các link `<a href...>` như bình thường mà sẽ cào thẳng text nội dung của các selector (`card_selector`) đang hiển thị trên trang.
   
2. **Auto-Scroll Limit**:
   Thêm cờ `auto_scroll_count` vào cấu hình. Hệ thống sẽ giới hạn chỉ scroll xuống N lần (ví dụ: 1-3 lần) và chờ 2s mỗi lần để chống bị đánh dấu là bot cào dữ liệu tốc độ cao. Đồng thời có giới hạn `max_items`.

3. **Session Cookies Management**:
   Cấu hình `cookie_file` trỏ tới file JSON chứa states của Playwright/CloakBrowser. Nếu file tồn tại, context mới sẽ được load kèm session này.

4. **Fake URL bằng Hashing**:
   Vì bài đăng Feed không có URL trực tiếp, sử dụng MD5 Hash của 50 ký tự đầu tiên làm định danh: `{index_url}#feed-{hash}` để hệ thống Dedup có thể xử lý và không lưu trùng lặp.

## Risks / Trade-offs

- **Risk - Bị khóa tài khoản (Ban Account):** Việc dùng cookie thật để cào LinkedIn/X tiềm ẩn rủi ro khóa tài khoản nếu cấu hình `auto_scroll_count` hoặc tần suất schedule quá dày.
  *Mitigation:* Cần khuyến cáo Admin cấu hình tần suất Ingestion thưa (ví dụ 6-12 tiếng/lần) và giới hạn `max_items` thấp (VD: 5 bài).
- **Trade-off - Độ ổn định của Selector:** Cấu trúc DOM của LinkedIn/X thay đổi liên tục. Nếu họ đổi class name của Card, tính năng này sẽ hỏng tạm thời.
  *Mitigation:* Sử dụng selector linh hoạt hoặc liên tục theo dõi logs hệ thống.
