## Why

Hiện tại, chất lượng dịch thuật và tóm tắt tiếng Việt của mô hình AI Gemini (Module M4 - AI Analysis) đang gặp hiện tượng lặp khuôn mẫu (văn phong dịch máy sáo rỗng). AI thường xuyên lặp lại các cụm từ mở đầu giống nhau như: *"Đối với các team phát triển phần mềm Việt Nam..."*, *"Điều này quan trọng vì..."* hoặc *"Tin này có ý nghĩa..."*. Những khuôn mẫu lặp đi lặp lại này làm giảm đi tính tự nhiên, độ sắc bén và giá trị thực tế của bản tin tình báo công nghệ.

Cần cải tiến hệ thống prompt trong Backend thông qua hai kỹ thuật nâng cao:
1. **Ràng buộc tiêu cực (Negative Constraints / Negative Prompting):** Chỉ định rõ danh sách các cụm từ sáo rỗng bị cấm sử dụng để buộc mô hình phải diễn đạt tự nhiên hơn.
2. **Học qua ví dụ (Few-shot Prompting):** Cung cấp 2-3 mẫu phân tích tóm tắt mẫu mực (được biên soạn bởi chuyên gia con người) trực tiếp vào ngữ cảnh để AI học tập văn phong sắc sảo, ngắn gọn và tập trung vào hành động thực hành.

## What Changes

1. **Backend Prompting (`backend/app/ai/prompts.py`):**
   - Cập nhật biến `ANALYSIS_PROMPT` để thêm quy tắc cấm sử dụng các tiền tố lặp đi lặp lại (cụ thể: cấm mở đầu phần tóm tắt bằng các từ mang tính giải thích lý do hiển nhiên).
   - Tích hợp 2 ví dụ Few-shot chất lượng cao mô phỏng cấu trúc đầu ra JSON mong muốn (bao gồm: tiêu đề dịch tự nhiên, bullets thực hành ngắn gọn, signal sắc bén).
   - Giữ nguyên giới hạn 6,000 ký tự đầu vào để tránh việc Few-shot chiếm quá nhiều token và làm mất ngữ cảnh bài viết gốc.

## Capabilities

### New Capabilities
- Không có.

### Modified Capabilities
- `ai-analysis`: Cải thiện chất lượng bản dịch và tóm tắt tiếng Việt của AI, loại bỏ khuôn mẫu dịch tự động sáo rỗng.

## Impact

- **Backend:**
  - File [prompts.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/ai/prompts.py) — Cập nhật cấu trúc prompt `ANALYSIS_PROMPT`.

- **Frontend:** Không thay đổi.

- **Non-goals:**
  - Không thay đổi cấu trúc schema JSON trả về từ Gemini (`AnalysisResult` và các trường Pydantic) để tránh làm vỡ logic phân tích hiện tại của backend.
  - Không thay đổi model AI đang sử dụng (vẫn giữ nguyên Gemini 2.5 Flash).
