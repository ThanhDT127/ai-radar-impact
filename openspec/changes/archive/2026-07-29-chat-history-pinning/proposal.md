## Why

`chat-context-depth` (28/07/2026) đảo ngược cô lập luồng và tuyên bố một bất biến thay thế:
*mọi tin được nhắc trong history đều còn mặt trong ngữ cảnh của lượt hiện tại — hoặc trong
working set, hoặc trong index toàn hệ thống*. **Không có gì thực thi bất biến đó.** Working
set chỉ được thêm khi người dùng chủ động mở trang chi tiết hoặc **bấm** citation; index thì
do `_rank` của lượt hiện tại quyết, mà `_rank` chưa bao giờ nhìn thấy history.

Đo 29/07/2026 (6 chủ đề × 6 chủ đề, top-3 của `_rank` làm proxy cho tin đã trích):
**47/90 = 52%** số cặp (tin đã bàn, chủ đề mới) **rơi khỏi top-60**, tệ nhất là hạng
**118/179**. Tức hơn một nửa số lần chuyển chủ đề, `_history_block` đưa vào prompt cái *tên*
một tin mà prompt không còn *nội dung* nào của nó. Grounding fail-closed chặn được bịa đặt,
nên hậu quả là bot từ chối chuyện nó vừa tự nói — an toàn nhưng hỏng trải nghiệm.

## What Changes

- Tin từng được trích dẫn trong `history` được **ghim** vào index của lượt hiện tại, bất kể
  thứ hạng `_rank`. Chọn theo **thứ tự nhắc gần nhất**, tất định, không chấm điểm.
- Chỗ ghim nằm **trong** `chat_index_top_k` (đẩy đuôi bảng xếp hạng ra), giữ nguyên bất biến
  ngân sách token đã có với ô sâu: *`index_limit` là TỔNG số tin vào prompt*.
- `ChatTurn.citations` (đã có `n` + `title`) bổ sung định danh để server ghim được. Đây là
  **BREAKING** với ghi chú "không mang `insight_id` — mọi thứ thừa hơn thế là bề mặt tấn
  công" trong `schemas/chat.py`; design phải chọn giữa client gửi id và server tự tra theo
  title, và nêu rõ đánh đổi bảo mật.
- Số chỗ ghim mặc định **3**, cấu hình qua env; trùng số với `chat_deep_slots` và `MAX_REFS`.

## Capabilities

### New Capabilities
<!-- Không có: đây là siết chặt một bất biến đã tuyên bố, không phải năng lực mới. -->

### Modified Capabilities
- `chat-qa-service`: thêm yêu cầu *tin đã trích trong lịch sử hội thoại luôn có mặt trong
  ngữ cảnh lượt hiện tại*, và ràng buộc *chỗ ghim nằm trong trần index*.

## Non-goals

- **KHÔNG** nén / tóm tắt lịch sử hội thoại. Bản To-Be yêu cầu nén lượt 4–10 thành một dòng;
  đo 29/07 cho thấy history đầy trần chỉ chiếm **3,8%** prompt (1.713/45.228 ký tự), mà cắt
  hẳn 30% prompt đã đo là **không đổi TTFT**. Nén chữa một vấn đề không tồn tại, tốn thêm một
  lượt gọi model, và **làm ca trên tệ hơn** vì vứt bớt chi tiết của đúng phần đang thiếu chỗ
  dựa. Hạng mục này chuyển từ "hoãn" sang **bác bỏ có lý do đo được**.
- **KHÔNG** đưa tin ghim vào ô sâu. Ô sâu là chỗ của working set do người dùng chủ động chọn;
  tin trong history là thứ *đã bàn qua*, cần **có mặt** chứ chưa chắc cần **đọc kỹ**. Trộn hai
  loại là xoá ranh giới mà `chat-context-depth` vừa dựng.
- **KHÔNG** sửa `_rank`, `_relevance`, `_question_terms` hay công thức RRF. Ghim là bước
  **sau** xếp hạng. Giữ vậy để không phải chốt lại baseline RS.
- **KHÔNG** tự động thêm tin đã trích vào working set (phương án B đã cân nhắc): chip tự mọc
  mà người dùng không bấm gì là đổi hành vi UI thấy được — quyết định sản phẩm, không thuộc
  change này.

## Phase

**Phase 2** — siết chặt chất lượng hội thoại đa lượt, sau khi khung retrieval (⑥ hybrid,
chunk) và context depth đã land.

## Dependencies

- **`chat-context-depth` (28/07/2026)** — cứng. Change này thực thi đúng bất biến mà nó
  tuyên bố; không có working set + ô sâu thì không có gì để siết.
- **`chat-rank-stability`** — RS harness là cổng đo. Đã chạy trước: recall@K giữ **0,968** và
  recall@5 giữ **0,900** ở K hiệu dụng 57/55/54, gãy ở 53 (một `must_have` nằm ở hạng 54).
  Ghim 3 ⇒ biên an toàn 3 hạng.
- **`chat-eval-quality-gate`** — `chat_answer_harness --live` **bắt buộc** chạy lại sau khi
  implement: đổi context là đổi câu trả lời, và RS không đo được việc model có bị 3 dòng tin
  cũ kéo lạc đề ở câu hỏi mới hay không.

## Impact

- `backend/app/services/chat_service.py` — `_answer_global`, đường truyền history xuống context
- `backend/app/services/chat_grounding.py` — `build_context` (hàm thuần, RS harness phụ thuộc)
- `backend/app/schemas/chat.py` — `TurnCitation`
- `backend/app/config.py` — biến số chỗ ghim
- `frontend/src/api/chat.ts`, `ChatWidget.tsx` — nếu chọn phương án client gửi định danh
- Bộ đo: `tests/eval/chat_rank_harness.py` (K hiệu dụng), `chat_answer_harness` (chạy `--live`)
