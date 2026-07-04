## 1. Cập nhật Prompts trong Backend

- [x] 1.1 Sửa đổi file [prompts.py](file:///d:/Works/AI%20Radar%20Impact/backend/app/ai/prompts.py) để bổ sung phần chỉ dẫn Negative Constraints (loại bỏ các cụm từ mở đầu sáo rỗng)
- [x] 1.2 Thiết kế và bổ sung 2 ví dụ Few-shot chất lượng cao (cấu trúc Input/Output JSON mẫu) vào prompt chính `ANALYSIS_PROMPT`

## 2. Kiểm thử và Xác thực Chất lượng AI Output

- [x] 2.1 Chạy thử nghiệm phân tích tin tức trên môi trường local bằng lệnh `docker-compose exec backend python -m app.scripts.run_analysis`
- [x] 2.2 Đánh giá dữ liệu tóm tắt được sinh ra trong DB (hoặc qua giao diện Dashboard) để xác nhận văn phong tiếng Việt tự nhiên, không bị rập khuôn dịch máy
- [x] 2.3 Đảm bảo API backend không bị crash và không gặp bất kỳ lỗi parse JSON hoặc ValidationError nào khi nhận kết quả từ Gemini

