# Tasks: chat-answer-completeness

**Phase:** 2 (M8 Chatbot). Backend + Test — một file code, không migration, không đụng Frontend.

> Thứ tự: nâng trần (rẻ nhất) → tách hàm để dùng lại vòng retry 429 → hỏi lại → lưới an toàn → test.

## 1. Tuyến phòng thủ 1 — trần output (Backend)

- [x] 1.1 `CHAT_MAX_OUTPUT_TOKENS` 4096 → 8192, kèm comment nêu rõ token chỉ bị tính tiền khi **thực sinh** nên trần cao không đắt hơn cho câu ngắn. **DoD:** người đọc sau không tưởng đây là đánh đổi chi phí.

## 2. Tuyến phòng thủ 2 — hỏi lại (Backend)

- [x] 2.1 Tách `_chat_once()` khỏi `chat()`, trả `(text, bị_cắt, calls)`; vòng retry 429 (3s/10s) nằm trong `_chat_once` để **cả hai** lượt đều được bảo vệ. **DoD:** không nhân đôi logic retry.
- [x] 2.2 `_CONCISE_RETRY_DIRECTIVE` — ràng buộc **độ dài trình bày**, nói rõ "phủ ĐỦ Ý đã hỏi". **DoD:** chỉ dẫn không chứa bất kỳ câu nào thu hẹp phạm vi trả lời.
- [x] 2.3 `chat()` gặp cắt → gọi `_chat_once()` lần hai với `system_prompt + _CONCISE_RETRY_DIRECTIVE`, câu hỏi giữ **nguyên văn**. **DoD:** test khẳng định `user_prompt` hai lượt bằng nhau.
- [x] 2.4 Hỏi lại đúng **một** lần, không leo thang nhiều bậc. **DoD:** tối đa 2 lượt/câu — vừa khít `MAX_MODEL_CALLS_PER_QUESTION=2`.
- [x] 2.5 Cộng `calls` của lượt hỏi lại vào giá trị trả về. **DoD:** budget khớp số lượt thực tốn tiền.
- [x] 2.6 Lượt hỏi lại trả rỗng → giữ bản đầu (đã cắt gọn) thay vì trả chuỗi rỗng. **DoD:** không bao giờ trả về câu trả lời trống.

## 3. Tuyến phòng thủ 3 — lưới an toàn (Backend)

- [x] 3.1 `_trim_to_last_sentence()` cắt tại `.!?…` cuối cùng; không có ranh giới nào thì trả nguyên văn. **DoD:** cắt bừa còn tệ hơn giữ nguyên.
- [x] 3.2 **Gỡ hẳn** chuỗi `_(Câu trả lời bị cắt vì quá dài — bạn thử hỏi hẹp hơn nhé.)_` khỏi code chạy. **DoD:** grep `backend/app/` không còn; chỗ duy nhất còn nhắc là `tests/test_chat_truncation.py`, nơi nó là hằng số để khẳng định marker KHÔNG xuất hiện.

## 4. Test (Test)

- [x] 4.1 Đường sung sướng: không cắt → nguyên văn, đúng 1 lượt, KHÔNG hỏi lại. **DoD:** `tests/test_chat_truncation.py`.
- [x] 4.2 Cắt lần đầu → trả bản hỏi lại, `calls == 2`. **DoD:** khẳng định cả nội dung lẫn số lượt.
- [x] 4.3 Lượt hỏi lại mang ràng buộc độ dài và giữ nguyên câu hỏi. **DoD:** so sánh `system_instruction` + `contents` của hai lượt.
- [x] 4.4 **Parametrize qua cả 3 nhánh**: khẳng định marker cũ KHÔNG xuất hiện ở bất kỳ nhánh nào. **DoD:** đây là bất biến chính của change.
- [x] 4.5 Hỏi lại vẫn cắt → lùi về ranh giới câu. **DoD:** không kết thúc giữa từ.
- [x] 4.6 Hỏi lại rỗng → giữ bản đầu đã cắt gọn. **DoD:** không trả chuỗi rỗng.
- [x] 4.7 `_trim_to_last_sentence` 5 ca + ca không có ranh giới. **DoD:** phủ `.`/`!`/`?`/`…`/gạch đầu dòng.

## 5. Tài liệu

- [x] 5.1 `CLAUDE.md` mục chat: nêu rõ hành vi cũ **sai ở đâu** (giao câu trả lời thiếu vế sau, đẩy việc sửa sang người dùng), không chỉ mô tả hành vi mới. **DoD:** người đọc sau không "tối ưu" ngược lại.
