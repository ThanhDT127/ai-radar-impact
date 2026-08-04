# Tasks: chat-intent-router

**Phase:** 2 (M8 Chatbot). Toàn bộ Backend + Test — không đụng Frontend, không migration, không n8n.

> Thứ tự: viết bộ phân loại + preset → chèn vào `answer()` trước cửa quota → test (viết ca fall‑through
> TRƯỚC để chắc không gạt nhầm câu thật) → docs.

## 1. Bộ phân loại ý định (Backend)

- [x] 1.1 Viết hàm phân loại deterministic (helper trong `chat_service.py` hoặc `intent.py` mới): trả về nhóm ý định `salutation` / `capability` / `thanks` / `None` (None = câu thật, fall‑through). Nhận diện bằng cách bỏ token thuộc tập chào/meta + `_STOPWORDS` khỏi câu; **rỗng phần còn lại → nhóm tương ứng; còn nội dung → None** (design D2). **DoD:** `"chào bạn"`→salutation; `"cảm ơn nhé"`→thanks; `"bạn làm được gì"`→capability; `"chào, tuần này có gì cho Security"`→None.
- [x] 1.2 Bảng preset tĩnh tiếng Việt cho từng nhóm, `citations=[]`. Preset `capability` phải **điều hướng**: nêu ví dụ truy vấn tốt (vd "tuần này có gì cho Security?") (design D4). **DoD:** mỗi nhóm có một preset; không nhóm nào trả chuỗi rỗng.
- [x] 1.3 Tập token chào/meta khởi đầu nhỏ và chắc chắn (`chào`, `hi`, `hello`, `xin`, `cảm ơn`, `thanks`, `ai`(trong "bạn là ai") — cẩn thận trùng từ khoá; xét theo cụm), có comment "mở rộng theo log, đừng đoán trước". **DoD:** đọc code biết cách mở rộng an toàn.

## 2. Chèn vào luồng answer (Backend)

- [x] 2.1 Trong `ChatService.answer()`, chạy phân loại ý định **trước cửa quota** (design D3). Nhóm ≠ None → trả `{answer: preset, citations: [], mode: "meta"}`, ghi `chat_logs` với `model_calls=0`, **không** kiểm/không tiêu quota. **DoD:** hỏi "xin chào" khi `max_daily_chat_calls` đã cạn vẫn nhận preset, không 429.
- [x] 2.2 Nhóm None → giữ nguyên đường cũ: kiểm quota → mode B/A → 1 lượt gọi. **DoD:** câu hỏi thật hành xử y hệt trước change này.
- [x] 2.3 Cập nhật comment `mode` trong `schemas/chat.py` thành `"insight" | "global" | "meta"`. **DoD:** comment khớp giá trị thật service trả.
- [x] 2.4 Fast‑path chạy cho cả khi có `insight_id` (chào trong lúc mở một bài vẫn là chào). **DoD:** gửi "chào" kèm `insight_id` hợp lệ → preset, 0 call, không nạp bài gốc.

## 3. Test (Test)

- [x] 3.1 Ca fall‑through (viết TRƯỚC): "chào, tuần này có gì cho Security", "cảm ơn vì tin về mã nguồn mở" → **None** → đi pipeline. **DoD:** khẳng định các câu này KHÔNG bị fast‑path; nếu luật gạt nhầm thì test đỏ.
- [x] 3.2 Ca fast‑path: "xin chào", "bạn làm được gì?", "cảm ơn" → mode meta, `citations=[]`, **0 lượt gọi model** (mock Gemini, assert không được gọi). **DoD:** assert số lần gọi client Gemini = 0 cho các ca này.
- [x] 3.3 Ca quota cạn + chào: giả lập `sum_model_calls_today >= cap` → hỏi "xin chào" → vẫn nhận preset (không 429); hỏi câu thật → 429. **DoD:** hai nhánh phân biệt rõ.
- [x] 3.4 Ca log: fast‑path ghi `chat_logs` với `model_calls=0`; bộ đếm `SUM(model_calls)` không đổi. **DoD:** một fast‑path không làm tăng budget đã dùng.

## 4. Tài liệu (làm sau khi code đã chạy)

- [x] 4.1 Thêm vào `CLAUDE.md` mục chat: fast‑path chào/meta trả preset **0 gọi model**, **không tính quota** và **không bị quota chặn**; `mode="meta"`; phân loại là **deterministic** (đừng đổi sang LLM). **DoD:** người đọc hiểu vì sao chỗ này không được dùng model.
- [x] 4.2 Ghi một dòng: Query Reformulator **chưa làm**, phụ thuộc streaming ⑤ (tránh người sau tưởng đã có). **DoD:** đọc CLAUDE.md không nhầm là reformulator đã tồn tại.
