# Tasks: chat-intent-hybrid-filter

**Phase:** 2 (M8 Chatbot). Backend + Test — không đụng Frontend, không migration.

> Thứ tự thực tế đã làm: **đo trước, thiết kế sau**. Ba phép đo (sàn round-trip, độ chính xác của model
> trên toàn tập, độ chính xác của luật) là thứ bác bỏ phương án "giao hết cho model" — không có chúng thì
> change này đã đi sai hướng.

## 1. Đo nền trước khi viết code

- [x] 1.1 Dò model lite khả dụng trên Vertex `us-central1`. **DoD:** biết chắc model nào dùng được — kết quả: `gemini-2.5-flash-lite` là lựa chọn duy nhất, `gemini-2.0-flash-lite` + bản preview đều 404.
- [x] 1.2 Đo sàn round-trip với prompt rỗng + 1 token output. **DoD:** có con số cận dưới không thể tối ưu — kết quả **1.433 / 1.536 / 1.685 ms**.
- [x] 1.3 Xác nhận `gemini-2.5-flash` KHÔNG dùng được để phân loại. **DoD:** đo được nó trả text rỗng ở `max_output_tokens=8` vì thinking ăn hết ngân sách.
- [x] 1.4 Chấm model trên toàn bộ 84 ca nhãn tay. **DoD:** có precision/recall để so với luật — kết quả precision **91,5%** (4 FP), recall 100%.
- [x] 1.5 Chấm luật tất định trên cùng tập. **DoD:** so sánh được hai phương án trên cùng thước — luật precision 97,6%, recall 95,3%.

## 2. Tầng 1 — luật ba trạng thái (Backend)

- [x] 2.1 `route_intent()` trả nhóm ý định / `None` / `AMBIGUOUS`; `classify_intent()` thành wrapper mỏng quy `AMBIGUOUS` về `None`. **DoD:** test cũ của `chat-intent-router` vẫn xanh không sửa.
- [x] 2.2 `_SELF_TOKENS` + `_SELF_PHRASES` — tín hiệu tự quy chiếu về bot. `trợ lý` khớp theo **cụm**, vì token `trợ` đơn lẻ còn nằm trong "hỗ trợ". **DoD:** "bạn hoạt động thế nào" → capability; "hỗ trợ gì" KHÔNG → capability.
- [x] 2.3 `_ANAPHORA_TOKENS` — đại từ hồi chỉ không kèm tự quy chiếu ⇒ câu tra cứu, quyết dứt điểm ở tầng 1. **DoD:** "nó là ai", "công cụ này hỗ trợ gì", "mô hình này có khả năng gì" → `None`.
- [x] 2.4 `_CAPABILITY_CONTENT_TOKENS` **suy ra tự động** từ `_CAPABILITY_PHRASES`. **DoD:** thêm một cụm mới là token nội dung của nó tự có mặt — cụm chết không tái sinh được.
- [x] 2.5 Dọn code chết: bỏ cụm `"dùng để làm gì"` (hậu tố của `"để làm gì"`, không bao giờ khớp thêm câu nào). **DoD:** mọi cụm còn lại đều tới được (kiểm bằng probe "bạn " + cụm).
- [x] 2.6 Thêm `you`, `nhiều` vào `_FILLER_TOKENS`. **DoD:** "thank you", "cảm ơn nhiều" → thanks.

## 3. Tầng 2 — model nhẹ (Backend)

- [x] 3.1 `GeminiClient.classify_intent()` dùng `settings.intent_classifier_model_id`. **DoD:** trả nhóm ý định hoặc `None`.
- [x] 3.2 Cấu hình tối ưu TTFT: nhãn một ký tự (`INTENT_LABELS`), `max_output_tokens=4`, `temperature=0.0`, **không retry**. **DoD:** test khẳng định từng tham số.
- [x] 3.3 `INTENT_CLASSIFIER_PROMPT` có phần QUY TẮC phân biệt "hỏi về bot" với "hỏi về sản phẩm trong bài". **DoD:** prompt tự đứng vững kể cả khi tập lưỡng lự đổi.
- [x] 3.4 Fail-safe: mọi exception / nhãn lạ → `None` + log warning, KHÔNG ném ra ngoài. **DoD:** test với fake ném `RuntimeError` vẫn trả `None`.
- [x] 3.5 Hai setting mới trong `config.py`: `intent_classifier_model_id`, `intent_classifier_enabled`. **DoD:** tắt được tầng 2 mà không sửa code.

## 4. Nối hai tầng (Backend)

- [x] 4.1 `ChatService._route_intent()` — tầng 1 trước, tầng 2 chỉ khi `AMBIGUOUS`, bọc `asyncio.to_thread` (chat nằm trên request path). **DoD:** không chặn event loop.
- [x] 4.2 Lượt gọi tầng 2 KHÔNG cộng vào `model_calls`. **DoD:** fast-path qua tầng 2 vẫn ghi `chat_logs` với `model_calls=0`.
- [x] 4.3 `intent_classifier_enabled=False` → `AMBIGUOUS` rơi về pipeline. **DoD:** test khẳng định model không bị gọi.

## 5. Test (Test)

- [x] 5.1 Tầng 1 ba trạng thái: ca chắc chắn preset, ca chắc chắn câu thật, ca lưỡng lự. **DoD:** `tests/test_chat_intent_hybrid.py`.
- [x] 5.2 Ca hồi chỉ (7 ca) → `None`. **DoD:** khoá đúng ca mà cả matching cũ lẫn flash-lite đều sai.
- [x] 5.3 **Cổng chặn hồi quy tỉ lệ lưỡng lự ≤ 10%.** **DoD:** ai nới luật làm tập lưỡng lự phình ra thì test đỏ — vì mỗi ca thêm là +1,5s.
- [x] 5.4 Tầng 2: ánh xạ nhãn, nhãn lạ, model lỗi, tham số gọi. **DoD:** 4 nhóm test riêng.
- [x] 5.5 Nối tầng: luật chắc chắn thì KHÔNG gọi model nhẹ (4 ca parametrize). **DoD:** đây là bất biến đắt nhất — gọi thừa = +1,5s cho câu vốn miễn phí.
- [x] 5.6 Đo lại bộ lai live trên 84 ca. **DoD:** precision **100%**, recall **97,7%**, chạm tầng 2 **3,6%**.

## 6. Tài liệu

- [x] 6.1 Sửa `CLAUDE.md`: dòng "**Phân loại là deterministic — ĐỪNG đổi sang LLM classifier**" nay đã sai. **DoD:** thay bằng mục hai tầng kèm số đo và lý do không giao hết cho model.
- [x] 6.2 Ghi số đo sàn round-trip vào `CLAUDE.md`. **DoD:** người đọc sau hiểu vì sao không được "cho nhanh thì đưa hết cho model".
