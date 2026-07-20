# Ghi chú phát hành — fix-insight-count-is-primary

## Con số trên dashboard giảm — đây là SỬA LỖI, không phải mất dữ liệu

Trước đây các bộ đếm đếm cả bản trùng mà danh sách vốn đã ẩn đi, nên số hiển thị luôn
lớn hơn số thẻ bấm vào xem được. Không insight nào bị xóa; chỉ có cách đếm được sửa cho
khớp với những gì thực sự hiển thị.

| Chỗ hiển thị | Trước | Sau |
|---|---|---|
| KPI "Tổng insight" | 71 | 64 |
| KPI "Cơ hội" | 64 | 57 |
| KPI "Nghiêm trọng/Cao" | 3 | 3 (không đổi) |
| Chip `LinkedIn - OpenAI` | 5 | 2 |
| Chip `HF Zhipu (GLM)` | 3 | 1 |
| Chip `HF Qwen` | 3 | 2 |
| Chip `HF DeepSeek` | 2 | 1 |

Triệu chứng cũ dễ nhận nhất: chip nguồn báo 5 bài nhưng bấm vào chỉ hiện 2.

Nguồn mà **toàn bộ** insight đều là bản trùng nay hiện count 0 và xuống nhóm "chưa có
insight". Nguồn đó vẫn cào được bài — chỉ là mọi bài đều trùng với nguồn khác.
