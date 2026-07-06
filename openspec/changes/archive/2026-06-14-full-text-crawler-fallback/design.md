## Context

Trình thu thập dữ liệu hiện tại (Module M2: Ingestion) của AI Impact Radar đối với các luồng RSS đang chỉ lấy được tóm tắt (snippet) thay vì nội dung gốc. Hậu quả là ở Module M4 (AI Analysis), mô hình Gemini Flash 2.0 thiếu hụt ngữ cảnh trầm trọng, làm giảm chất lượng output của quá trình phân loại, đánh giá mức độ ảnh hưởng (impact mapping) và sinh tóm tắt. Khó khăn lớn nhất là các nguồn dữ liệu mục tiêu (GitHub, HuggingFace) áp dụng các biện pháp chặn bot tự động.

## Goals / Non-Goals

**Goals:**
- Lấy được toàn bộ nội dung (full-text) của các bài viết từ RSS khi nội dung snippet quá ngắn (< 500 ký tự).
- Vượt qua cơ chế chống bot bằng trình duyệt thật (Playwright kết hợp CloakBrowser qua giao thức CDP).
- Cải thiện chất lượng dữ liệu đầu vào cho bảng `raw_documents`.

**Non-Goals:**
- Không thay đổi các API endpoints hiện có.
- Không thay đổi luồng gửi thông báo (n8n integration ở Module M7).
- Không bóc tách bảng biểu, hình ảnh, video (giữ `include_tables=False` trong Trafilatura).

## Decisions

- **Affected Module:** M2 (Ingestion).
- **Database Affected:** Bảng `raw_documents` sẽ phải chứa lượng dữ liệu lớn hơn rất nhiều ở cột `raw_content` (từ vài trăm ký tự lên vài chục nghìn ký tự).
- **AI / LLM:** Giữ nguyên mô hình Google Gemini Flash 2.0 tại M4, nhưng chất lượng grounding sẽ tốt hơn nhờ có đủ ngữ cảnh.
- **Implementation Detail:** Tích hợp logic xử lý vào `rss_connector.py`. Nếu độ dài content thu được từ feedparser < 500 ký tự, gọi luồng fallback sử dụng `playwright_connector.py` kết nối tới `http://cloak:9222` (CloakBrowser CDP). Đợi trang load xong DOM (`domcontentloaded`) rồi lấy HTML đưa qua `trafilatura.extract()` để lấy văn bản thuần túy.

## Risks / Trade-offs

- **Tốc độ thực thi (Performance):** Việc gọi Playwright khởi tạo headless browser và fetch HTML mất nhiều thời gian hơn rất nhiều (có thể từ 10-30s cho mỗi URL bị fallback) so với việc chỉ đọc RSS XML. Do đó, cần cấu hình timeout rõ ràng (ví dụ: 45s) cho luồng Thread chạy Playwright để tránh treo Ingestion Scheduler.
- **Tiêu thụ tài nguyên:** Đòi hỏi container `cloakbrowser` phải luôn chạy và tiêu tốn nhiều RAM/CPU hơn trình HTTP client thông thường.
