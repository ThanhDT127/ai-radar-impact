## Why

Quá trình Ingestion hiện tại lấy về một lượng lớn dữ liệu "nhiễu" từ các trang tin tức công nghệ và mạng xã hội. Các bài viết PR ra mắt sản phẩm mới không kèm tài liệu kỹ thuật, các thông báo sa thải nhân sự (ví dụ: Meta sa thải nhân viên), hay các tin đồn chưa được kiểm chứng làm loãng Insight Pipeline và gây tốn kém chi phí gọi API LLM (M4). Đồng thời, các bài báo học thuật cốt lõi (Research Papers) bị đánh giá điểm thấp và bị loại bỏ sai vì không mang tính ứng dụng thực tế ngay lập tức. Các lệnh cấm vận công nghệ cũng bị loại sai nếu không được coi là lỗi bảo mật.
Hệ thống cần phân hóa mạnh mẽ thông tin thu thập ngay từ vòng cửa ngõ (GATE).

## What Changes

Cải tiến toàn diện `GATE_PROMPT` trong module AI Analysis (M4):
- **Áp dụng Burden of Proof (Bằng chứng cụ thể):** Bắt buộc bài viết phải chứa link mã nguồn, code snippets, CVE ID, luật định rõ ràng, hoặc số liệu benchmark có cơ sở. Nếu chỉ là lời nói suông từ PR, đánh rớt (Score: 0.1).
- **Thêm Academic Exception (Ngoại lệ học thuật):** Các bài báo khoa học, paper nghiên cứu tuy điểm khả thi thấp nhưng sẽ được gán cờ `Theoretical` và cho qua (Score: 0.2 - 0.4).
- **Thêm Disruption Exception (Ngoại lệ rủi ro đứt gãy):** Tin tức về cấm vận công nghệ, chặn IP, khai tử (deprecated) các dịch vụ AI lớn phải lọt qua với cờ `Practical` (Score >= 0.7) để cảnh báo người dùng.

## Capabilities

### New Capabilities
- `prompt-differentiation`: Khả năng sàng lọc nâng cao bằng AI, phân loại luồng tin tức thành 3 mức độ rõ rệt (Signal, Noise, Academic/Theoretical) để tối ưu chi phí và nâng cao chất lượng Insights.

### Modified Capabilities
- `insight-prompt-revamp`: Chỉnh sửa logic của `GATE_PROMPT` cũ, nâng cấp bộ tiêu chuẩn xét duyệt đầu vào của AnalyzerService.

## Impact

- **Mã nguồn bị ảnh hưởng:** `backend/app/ai/prompts.py` (chỉnh sửa `GATE_PROMPT` và `ANALYSIS_PROMPT`).
- **Hệ thống:** Module M4 (AI Analysis). Giảm thiểu lượng bài viết rác lưu vào DB, tăng độ chính xác của Insight được duyệt (Practical Insights). Cải thiện tỷ lệ giữ lại các bài Research Paper.
- **Dependencies:** Google Gemini Flash 2.0 (Vertex AI).

## Non-goals

- Không thay đổi kiến trúc cơ sở dữ liệu (Database Schema).
- Không ảnh hưởng đến Connector của Ingestion (M2). M2 vẫn cào tất cả dữ liệu thô, M4 là nơi lọc rác.

## Phase & Dependencies
- **Phase áp dụng:** Phase 1 (Data Quality Polish)
- **Dependencies:** API Gemini phải có khả năng hiểu ngữ cảnh văn bản dài để trích xuất được Proof (Bằng chứng).
