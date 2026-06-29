## Context

File `backend/app/ai/prompts.py` định nghĩa system prompt gửi tới Gemini để thực hiện phân tích và sinh ra cấu trúc JSON. Chúng ta cần tinh chỉnh nội dung prompt này để cải thiện chất lượng hành văn tiếng Việt, làm cho thông tin sắc bén hơn và tránh văn phong rập khuôn tự động.

## Goals / Non-Goals

**Goals:**
- Thêm phần hướng dẫn cấm (Negative Constraints) để loại bỏ các câu mở đầu thừa thãi, sáo rỗng.
- Thêm 2 ví dụ Few-shot (gồm Input là bài viết kỹ thuật thực tế và Output là JSON mẫu đã được tối ưu hóa văn phong bởi con người).
- Giữ nguyên cấu trúc JSON schema đầu ra để backend parser không bị ảnh hưởng.

**Non-Goals:**
- Không thay đổi model Gemini đang sử dụng.
- Không thay đổi cách gọi API Vertex AI/Gemini trong `gemini_client.py`.

## Decisions

### 1. Tích hợp Ràng buộc Tiêu cực (Negative Constraints)
Chúng ta sẽ thêm một khối chỉ dẫn nghiêm ngặt vào đầu hoặc cuối của `ANALYSIS_PROMPT` trong file [prompts.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/ai/prompts.py):
```markdown
NGUYÊN TẮC HÀNH VĂN TIẾNG VIỆT (BẮT BUỘC):
1. KHÔNG bắt đầu các phần tóm tắt, tín hiệu hay rủi ro bằng các tiền tố sáo rỗng, lặp khuôn như:
   - "Đối với các team...", "Đối với các kỹ sư..."
   - "Điều này quan trọng vì...", "Tin này quan trọng do..."
   - "Bài viết này nói về...", "Tài liệu này thảo luận về..."
2. Hãy đi thẳng trực tiếp vào chủ thể hành động và nội dung kỹ thuật cốt lõi (ví dụ: Thay vì viết "Đối với team DevOps, điều này quan trọng vì giúp tự động hóa...", hãy viết "Tự động hóa CI/CD thông qua 2FA giúp DevOps...").
3. Giữ các thuật ngữ chuyên ngành công nghệ bằng tiếng Anh thay vì cố dịch gượng ép sang tiếng Việt (ví dụ: deployment, pipeline, API, staging, production, container, framework...).
```

### 2. Xây dựng 2 Ví dụ Few-shot chất lượng cao
Ví dụ Few-shot cần có cấu trúc:
- `[VÍ DỤ 1 - INPUT]` (Đoạn text tiếng Anh ngắn gọn về công nghệ bảo mật npm staged publishing)
- `[VÍ DỤ 1 - OUTPUT]` (JSON kết quả tiếng Việt sắc sảo, không chứa các từ bị cấm, recommendations thực tế cho DevOps và Security)
- `[VÍ DỤ 2 - INPUT]` (Đoạn text tiếng Anh ngắn gọn về benchmark hiệu năng của Gemini 2.0 vs Llama 3)
- `[VÍ DỤ 2 - OUTPUT]` (JSON kết quả chứa các con số đo đạc cụ thể trong `bullets` và `has_benchmark: true`)

### 3. Quy trình chạy thử nghiệm để kiểm tra chất lượng
Sau khi sửa prompt, nhà phát triển có thể chạy lệnh:
```bash
docker-compose exec backend python -m app.scripts.run_analysis
```
Lệnh này sẽ phân tích các bài viết pending và lưu kết quả vào DB. Sau đó chúng ta có thể kiểm tra trực tiếp trên Dashboard hoặc qua database để xác nhận văn phong mới đạt chuẩn tự nhiên.

## Risks / Trade-offs

- **Tăng token đầu vào:** Việc thêm Few-shot prompt sẽ làm tăng lượng token đầu vào (khoảng 1,000 - 1,500 tokens). Tuy nhiên, Gemini 2.5 Flash có context window cực kỳ lớn và chi phí token đầu vào rất rẻ, do đó sự gia tăng này hoàn toàn không đáng kể so với lợi ích vượt trội về chất lượng văn phong bản dịch mang lại.
