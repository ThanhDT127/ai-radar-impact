## Why

Trình cào tin RSS mặc định chỉ lấy được đoạn tóm tắt ngắn (snippet) của bài viết (thường dưới 500 ký tự), khiến AI Gemini bị thiếu ngữ cảnh trầm trọng để phân tích Insight chính xác. Ngoài ra, các trang web công nghệ lớn như GitHub, HuggingFace sử dụng cơ chế chống bot (Anti-bot) chặn các luồng cào dữ liệu tự động. Việc thiếu hụt nội dung gốc (full-text) làm giảm độ chính xác của cơ chế phân loại sự kiện và đánh giá mức độ ảnh hưởng của AI.

## What Changes

- Tích hợp `CloakBrowser` (thông qua thư viện Playwright kết nối qua cổng CDP) vào `rss_connector.py` và `playwright_connector.py` để hoạt động như một trình duyệt thật, lách qua các hàng rào chống bot.
- Sử dụng thư viện `trafilatura` để quét cấu trúc HTML và tự động bóc tách toàn bộ nội dung văn bản gốc (Full-text) của bài báo.
- Cài đặt cơ chế Fallback: Nếu nội dung thu được từ luồng RSS quá ngắn (dưới 500 ký tự), tự động kích hoạt tiến trình Playwright + CloakBrowser để truy cập thẳng URL bài viết lấy nội dung đầy đủ.

## Capabilities

### New Capabilities
- `full-text-extraction`: Khả năng bóc tách toàn bộ văn bản từ trang web gốc thông qua việc bypass cơ chế anti-bot và trích xuất nội dung từ HTML.

### Modified Capabilities
- `rss-ingestion`: Nâng cấp luồng thu thập RSS, bổ sung cơ chế fallback tự động.

## Impact

- **Mã nguồn bị ảnh hưởng:** `backend/app/connectors/rss_connector.py`, `backend/app/connectors/playwright_connector.py`.
- **Hệ thống:** Cải thiện chất lượng dữ liệu của bảng `raw_documents`, cung cấp ngữ cảnh đầy đủ (lên tới hàng chục nghìn ký tự) cho quá trình LLM Classification ở module M4.
- **Dependencies:** Sử dụng thư viện `trafilatura` và cấu hình kết nối tới container `cloak` qua port `9222`.

## Non-goals

- Không bóc tách và lưu trữ bảng biểu (tables), hình ảnh, hay video (cấu hình `trafilatura` bỏ qua tables).
- Không xử lý vượt rào các trang web yêu cầu đăng nhập trả phí (Paywall).

## Phase & Dependencies
- **Phase áp dụng:** Phase 1 (MVP)
- **Dependencies:** Cần container `cloakbrowser` hoạt động độc lập trong Docker Compose.
