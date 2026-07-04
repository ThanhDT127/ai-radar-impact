## 1. Tinh chỉnh GATE_PROMPT

- [x] 1.1 Bổ sung điều kiện "Burden of Proof" (Bằng chứng cụ thể) vào phần cốt lõi của Prompt để bắt buộc Gemini phải tìm thấy code, CVE, benchmark, hoặc số liệu rõ ràng.
- [x] 1.2 Bổ sung "Ngoại lệ Học thuật" (Academic Exception) để bảo vệ các bài viết mang tính lý thuyết, thuật toán lõi (Research Papers).
- [x] 1.3 Bổ sung "Ngoại lệ đứt gãy" (Disruption Exception) để ưu tiên xử lý các lệnh cấm vận công nghệ hoặc deprecation của các model quan trọng.
- [x] 1.4 Hướng dẫn AI cách gán cờ `Theoretical` và `Practical` dựa trên kết quả lọt qua vòng ngoại lệ.

## 2. Kiểm thử và Đối soát

- [x] 2.1 Reset trạng thái của bài "Chính phủ Mỹ cấm Fable 5" về `pending`.
- [x] 2.2 Chạy lại kịch bản Ingestion & Analysis để kiểm chứng bài viết này được gán thành `Practical` và Insight Score >= 0.7 thành công.
- [x] 2.3 Quét kiểm tra thử các bài PR rác (VD: Meta sa thải) để đảm bảo chúng bị lọc bỏ chính xác bởi bộ luật Burden of Proof mới.
