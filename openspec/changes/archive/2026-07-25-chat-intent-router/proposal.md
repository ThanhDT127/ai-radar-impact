# Proposal: chat-intent-router

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — phủ phần 5 khung To‑Be: Intent & Rewrite, không thêm tính năng nặng).

## Why

Mọi câu hỏi hiện chạy trọn pipeline: lọc → xếp hạng → dựng index (mode A) hoặc nạp bài gốc (mode B) →
**một lượt gọi Gemini 5–22,6s** (đo thật, thinking tokens 121→3.791 token/câu). Kể cả câu **không cần
tra cứu gì** — "xin chào", "bạn làm được gì?", "cảm ơn" — cũng tốn đúng một lượt gọi đó, đếm vào
`max_daily_chat_calls` (200/ngày, cap global) và bắt người dùng chờ.

Báo cáo kiến trúc To‑Be gọi đây là **Intent Router** (mục 3.2 #4): câu chào/meta trả lời ngay bằng câu
định sẵn, **bỏ qua toàn bộ tìm kiếm DB và gọi model**, tiết kiệm 100% tài nguyên cho nhóm câu đó. Đây là
phần rẻ nhất và an toàn nhất của khung — thuần deterministic, 0 lượt gọi model thêm.

Phạm vi đã chốt (23/07/2026): **chỉ** fast‑path chào hỏi/meta + non‑search, **không** làm Query
Reformulator ở đợt này. Lý do: reformulator là *thêm* một lượt gọi model, mà lượt trả lời chính đã 5–22,6s
— nó chỉ có nghĩa khi độ trễ *cảm nhận* được che bằng streaming (`chat-streaming-sse`, ⑤). Trước đó,
khoảng trống recall của câu nối tiếp mù được chữa bằng bản gộp‑từ‑khoá tất định (0 gọi model), không phải
bằng reformulator. Xem Open Questions.

## What Changes

- **Fast‑path deterministic cho chào hỏi / meta / cảm ơn**: `ChatService` phân loại ý định bằng luật
  **trước** khi nạp dữ liệu hay gọi model; nhóm này trả câu định sẵn tiếng Việt, `citations` rỗng,
  `mode="meta"`, **0 lượt gọi model**.
- **Fast‑path không tiêu và không bị chặn bởi quota**: câu chào vẫn trả lời được kể cả khi
  `max_daily_chat_calls` đã cạn (vì nó không tốn gì).
- **Ghi log fast‑path (`model_calls=0`)** để đo tần suất thật — biến thứ đang vô hình thành đo được.
- **Phân loại thiên về fall‑through**: chỉ fast‑path khi câu **chỉ** là chào/meta; còn nội dung thực chất
  thì chạy pipeline như cũ. False‑positive (gạt nhầm câu thật) tệ hơn nhiều false‑negative (tốn 1 lượt).

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-qa-service`: service SHALL định tuyến ý định bằng luật trước khi truy vấn/gọi model; câu chào/meta
  SHALL trả câu định sẵn không gọi model, không tiêu quota.

## Non-goals

- **Không** Query Reformulator / viết lại câu nối tiếp — dời sau, phụ thuộc `chat-streaming-sse` (⑤).
- **Không** dùng LLM để phân loại ý định — làm vậy tái lập đúng chi phí/độ trễ đang cắt (design D1).
- **Không** cố nhận diện toàn bộ câu ngoài miền (toán, thời tiết…) bằng luật — không gian vô hạn, dễ sai;
  câu ngoài miền thật vẫn để grounding fail‑closed hiện có xử lý (design D5).
- **Không** đổi frontend, không đổi request/response shape (chỉ thêm giá trị `mode="meta"` — `mode` là
  `str` tự do, tương thích ngược).
- **Không** đổi grounding, hợp đồng `n`, hay thuật toán xếp hạng.

## Dependencies

- `chatbot-qa` (archive 22/07/2026) — `ChatService.answer()` và spec bị sửa thuộc change đó.
- **Độc lập với `chat-context-isolation` (①)** ở mức code: ① thuần frontend, change này thuần backend
  (`chat_service.py`). Land theo thứ tự nào cũng được.

## Impact

- **Backend**: `services/chat_service.py` (bước phân loại ý định trong `answer()` + preset responses),
  có thể tách helper `intent.py`; `schemas/chat.py` (comment `mode`), test mới.
- **Frontend**: không đụng (widget hiển thị `answer`/`citations` không branch theo `mode`).
- **Docs**: `CLAUDE.md` mục chat — thêm dòng về fast‑path 0‑call và việc nó không tính quota.
- **Không** đổi endpoint, không migration.
