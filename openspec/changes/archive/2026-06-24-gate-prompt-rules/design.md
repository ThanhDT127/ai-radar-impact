## Context

Hệ thống AI Radar Ingestion hiện tại (M2) đang lấy về quá nhiều tin rác (Noise) từ các nguồn tổng hợp. Các tin này đi qua bộ lọc `GATE_PROMPT` của Gemini (M4) và vẫn lọt vào danh sách Insights vì prompt cũ không yêu cầu khắt khe về bằng chứng kỹ thuật. Ngoài ra, việc thiết kế Prompt cũ vô tình chặn mất 2 loại thông tin quan trọng do không thuộc tính "thực hành ngay":
1. Bài báo học thuật (Research Paper) từ ArXiv, HuggingFace.
2. Các thông báo cấm vận công nghệ / khóa vùng truy cập (Region Block / Deprecation) của các ông lớn AI (Ví dụ: Mỹ cấm Fable 5).

## Goals / Non-Goals

**Goals:**
- Nâng cấp `GATE_PROMPT` để chặn đứng tin PR, marketing, tin tức nhân sự (sa thải, tuyển dụng).
- Đưa ra yêu cầu "Bằng chứng cụ thể" (Burden of Proof) bắt buộc Gemini phải tìm thấy trong bài viết trước khi chấm điểm cao.
- Thiết kế luồng cho "Ngoại lệ học thuật" (Academic Exception) để giữ lại các bài nghiên cứu lõi với phân loại `Theoretical`.
- Thiết kế luồng cho "Ngoại lệ rủi ro đứt gãy" (Disruption Exception) để giữ lại các lệnh cấm vận với phân loại `Practical` và gán nhãn `Critical/High Impact`.

**Non-Goals:**
- Không sửa file schema output của Gemini (Pydantic model của AnalyzerService vẫn giữ nguyên).
- Không thêm API gọi DeepSeek hay đổi Model khác, tiếp tục dùng Gemini Flash 2.0.

## Decisions

1. **Luật Burden of Proof:**
   Prompt sẽ chứa một section riêng liệt kê các bằng chứng hợp lệ: Code block rõ ràng, API specs, Link repo GitHub thật, CVE ID hợp lệ, đạo luật có lộ trình rõ ràng, benchmark có dữ liệu định lượng. Nếu thiếu các yếu tố này, Gemini bắt buộc đánh rớt bài xuống `noise` hoặc `low_signal`.

2. **Xử lý Ngoại lệ Học thuật (Academic):**
   Nếu văn bản mang đậm tính chất nghiên cứu hàn lâm (nhưng không có code ứng dụng thực tiễn ngay), Gemini được phép bỏ qua luật Burden of Proof thực tiễn, thay vào đó kiểm tra phương pháp nghiên cứu (Methodology) và đánh tag `Theoretical`. Điểm Confidence được giữ ở mức vừa phải (0.3 - 0.5) đủ để lọt vào hệ thống.

3. **Xử lý Ngoại lệ Đứt gãy (Disruption):**
   Nếu bài viết là lệnh cấm vùng, cấm API, hoặc công cụ ngừng hỗ trợ, Gemini sẽ không yêu cầu mã code chứng minh. Chỉ cần xác định thời hạn (deadline) và mức độ ảnh hưởng diện rộng, bài báo sẽ lập tức được đẩy thẳng thành `Practical` Insight và cảnh báo cần migrate hệ thống.

## Risks / Trade-offs

- **Trade-off - Rủi ro False Negative:** Việc thắt chặt bộ luật Burden of Proof có thể khiến Gemini lỡ tay xóa một số bài báo công nghệ có ích nhưng viết bằng ngôn ngữ quá phổ thông.
  *Mitigation:* Cần thiết kế Admin Dashboard để theo dõi các bài bị gán mác `low_signal` và tinh chỉnh Prompt định kỳ.
- **Trade-off - Chiều dài Prompt tăng:** Việc nạp thêm nhiều Exceptions sẽ làm Prompt dài hơn, tốn nhiều Tokens hơn cho mỗi lần gọi Vertex AI.
