## Context

`ChatService.answer()` (`chat_service.py:134`) hiện làm theo thứ tự: kiểm quota → chọn mode theo
`insight_id` → nạp dữ liệu → **một lượt gọi Gemini** (5–22,6s, thinking tokens). Không có nhánh nào cho
câu "không cần tra cứu". Câu chào cũng đi trọn đường đó.

Báo cáo To‑Be (mục 3.2 #4, sơ đồ phần 5 "Fast Salutation Route / Non‑search Handling") đề xuất một bước
**tiền truy vấn** phân loại ý định, cho câu chào/meta trả lời tức thì bằng câu định sẵn. Phạm vi đợt này
**chỉ** phần đó — phần Reformulator của cùng mục dời sau (chốt 23/07, phụ thuộc streaming ⑤).

**Module ảnh hưởng:** M8 (Chatbot/Search) — thuần backend.
**API endpoints:** `POST /api/v1/chat` — request/response **không đổi shape**; thêm giá trị `mode="meta"`
(cột `mode` là `str` tự do, client cũ không branch theo nó → tương thích ngược).
**Bảng DB:** không đụng, không migration. `chat_logs` nhận thêm bản ghi `model_calls=0` cho fast‑path.
**AI/LLM:** phân loại ý định **không gọi model** (design D1); fast‑path **không gọi model**. `CHAT_SYSTEM_PROMPT`,
grounding, hợp đồng `n` giữ nguyên.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Câu chào/meta/cảm ơn: 0 lượt gọi model, trả lời tức thì, không tiêu quota.
- Không gạt nhầm câu hỏi thật thành câu chào (bias fall‑through).
- Đo được tần suất fast‑path để biết nó tiết kiệm bao nhiêu.

**Non-Goals:**
- Không Query Reformulator (dời sau ⑤).
- Không LLM classifier.
- Không nhận diện toàn bộ câu ngoài miền bằng luật.
- Không đổi frontend/grounding/xếp hạng.

## Decisions

### D1 — Phân loại bằng **luật deterministic**, không bằng LLM

Một lượt gọi LLM để phân loại ý định sẽ tái lập đúng thứ đang cắt: +1 lượt gọi, +độ trễ, +bề mặt sai. Mà
tập câu cần bắt (chào/meta/cảm ơn) là **đóng và nhỏ** — luật đủ. Nhất quán với triết lý "retrieval do
server điều khiển, rẻ, tất định" của hệ (giống `_question_terms`, `_roles_in_question`).

*Đã cân nhắc:* prompt "siêu nhẹ" như báo cáo gợi ý. Bỏ — "nhẹ" vẫn là một lượt gọi Vertex, vẫn 1–3s + tiền,
cho thứ một `set` chuỗi giải quyết tức thì.

### D2 — Fast‑path chỉ khi câu **chỉ** là chào/meta; bias fall‑through

Rủi ro bất đối xứng:
- **False‑positive** (câu hỏi thật bị coi là chào → trả câu định sẵn "mình giúp được…"): người dùng hỏi
  thật bị gạt — **hỏng rõ**.
- **False‑negative** (câu chào lọt vào pipeline): tốn đúng 1 lượt gọi — **phiền nhẹ**.

Nên luật thiên hẳn về fall‑through. Cách nhận diện tái dùng token đã có: bỏ các token thuộc **tập chào/meta**
(`chào`, `hi`, `hello`, `xin chào`, `cảm ơn`, `thanks`, `bạn là ai`, `bạn làm được gì`, `giúp gì`…) và
`_STOPWORDS` khỏi câu; **nếu phần còn lại rỗng** → fast‑path; còn nội dung thực chất → chạy pipeline.

Kiểm bằng ca thật:
- `"chào bạn"` → sau khi bỏ token chào + stopword: rỗng → fast‑path ✅
- `"chào, tuần này có gì cho Security"` → còn `tuần/security/…` → fall‑through ✅ (đây chính là bài học
  biên‑từ của `_roles_in_question`: đừng khớp chuỗi con, xét trọn câu)
- `"cảm ơn nhé"` → rỗng → fast‑path ✅

### D3 — Fast‑path bỏ qua quota và **không bị quota chặn**

Hiện `answer()` kiểm quota **đầu tiên** rồi mới xử lý. Fast‑path 0‑call phải nằm **trước** cửa quota: câu
chào không tốn gì thì phải trả lời được kể cả khi `max_daily_chat_calls` đã cạn. Ngược lại, ghi log
`model_calls=0` cho fast‑path để đo tần suất — bản ghi 0 không ảnh hưởng bộ đếm (`SUM(model_calls)`), chỉ
để quan sát. Thứ tự mới trong `answer()`: **phân loại ý định → (nếu fast‑path) trả preset + log 0 → return;
ngược lại → kiểm quota → pipeline như cũ.**

### D4 — Preset là chuỗi tĩnh, có tính điều hướng, không citation

Câu định sẵn tiếng Việt, không sinh bằng model, `citations=[]`. Câu meta **hướng người dùng vào truy vấn
tốt**: gợi ý ví dụ như *"thử hỏi: tuần này có gì cho Security?"*. Mỗi nhóm ý định một preset (chào, hỏi năng
lực, cảm ơn). `mode="meta"` để phân biệt với câu trả lời grounded.

### D5 — Câu ngoài miền (không phải chào) vẫn để grounding hiện có lo

Không cố dựng luật bắt "toán/thời tiết/tán gẫu" — không gian vô hạn, luật sẽ vừa sót vừa gạt nhầm. Câu ngoài
miền thật đi vào pipeline, không khớp insight nào, và `CHAT_SYSTEM_PROMPT` + fail‑closed hiện có đã trả
"không tìm thấy trong hệ thống" một cách tử tế — tốn 1 lượt gọi, hiếm gặp, chấp nhận. Fast‑path chỉ gánh
nhóm **phổ biến và nhận diện chắc chắn**: chào/meta/cảm ơn.

## Risks / Trade-offs

- **[Luật chào sót phrasing lạ]** → Hậu quả chỉ là tốn 1 lượt gọi (false‑negative rẻ, D2). Mở rộng tập
  chào dần theo log fast‑path, không cần đoán trước cho đủ.
- **[Preset cứng nhắc, không "thông minh"]** → Đúng ý đồ: câu chào không cần thông minh, cần **rẻ và tức
  thì**. Preset điều hướng (D4) còn dạy người dùng hỏi tốt hơn.
- **[Thêm `mode="meta"` chạm client]** → `mode` là `str` tự do, widget không branch theo nó; chỉ thêm giá
  trị, không đổi/xoá. An toàn.
- **[Đo tần suất bằng log 0‑call]** → Không đội quota, không đội tiền; chỉ thêm dòng `chat_logs`. Nếu volume
  fast‑path rất lớn có thể cân nhắc sau, v1 chấp nhận.

## Migration Plan

1. Tách helper phân loại ý định (deterministic) + bảng preset trong `chat_service.py` (hoặc `intent.py`).
2. Chèn bước phân loại vào đầu `answer()` **trước** cửa quota (D3); fast‑path trả preset + log 0.
3. Test: các ca chào/meta/cảm ơn → 0 call, mode meta; ca "chào + nội dung" → fall‑through; ca quota cạn +
   chào → vẫn trả lời.
4. Docs: `CLAUDE.md` mục chat.

Rollback: không migration, không đổi API shape — revert commit là đủ. Bỏ bước phân loại thì mọi câu quay
về đi trọn pipeline như trước.

## Open Questions

- **Query Reformulator**: dời sau, **phụ thuộc `chat-streaming-sse` (⑤)** — chỉ đáng thêm một lượt gọi khi
  streaming đã che độ trễ cảm nhận về ~2–4s; trước đó chữa recall follow‑up bằng bản **gộp‑từ‑khoá tất
  định** (0 gọi model), có `chat-rank-stability` harness canh hồi quy. Quyết lại khi ⑤ land.
- **Ngưỡng tập chào**: khởi đầu bằng danh sách nhỏ chắc chắn; mở rộng theo log thật thay vì đoán trước.
- **Có nên preset khác nhau theo mode B/A không** (đang xem 1 bài vs toàn cục)? v1 dùng chung; cân nhắc nếu
  người dùng chào trong lúc mở một bài thì gợi ý hỏi về chính bài đó.
