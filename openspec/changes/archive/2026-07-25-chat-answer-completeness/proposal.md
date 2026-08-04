# Proposal: chat-answer-completeness

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot). Sửa hành vi đầu ra của `GeminiClient.chat()`.

## Why

Khi câu trả lời chạm `max_output_tokens`, chat dán một dòng vào cuối đoạn văn đứt giữa từ:

> `_(Câu trả lời bị cắt vì quá dài — bạn thử hỏi hẹp hơn nhé.)_`

Hung bác bỏ hành vi này (25/07/2026): *"điều này là không được phép, luôn phải trả về đủ, hoặc prompt lại
để trả lời ngắn gọn nhưng đủ ý"*.

Lý do kỹ thuật đứng sau: người dùng nhận một câu trả lời **thiếu vế sau**, mà với dạng câu hỏi hay chạm
trần nhất — "liệt kê tin bảo mật tuần này" — vế thiếu chính là phần đáng giá nhất (khuyến nghị, rủi ro).
Dòng xin lỗi không sửa được gì; nó chỉ đẩy việc sửa sang cho người dùng ("hỏi hẹp hơn") trong khi hệ
thống hoàn toàn tự xử được. Đây là lỗi *hành vi*, không phải lỗi hiển thị.

Bối cảnh làm nó dễ xảy ra: Gemini 2.5 tính **thinking tokens vào cùng ngân sách output**, đo thật
121→3.791 token/câu — nên trần 4096 bị chạm sớm hơn nhiều so với cảm giác.

## What Changes

- **Nâng trần output 4096 → 8192.** Token chỉ bị tính tiền khi **thực sinh**, nên trần cao hơn không đắt
  hơn cho câu ngắn — nó chỉ ngừng cắt oan câu dài. Đây là tuyến phòng thủ 1.
- **Chạm trần → hỏi lại**, kèm `_CONCISE_RETRY_DIRECTIVE`: gộp ý, tối đa 5 gạch đầu dòng, **đủ ý** —
  ràng buộc *độ dài trình bày*, KHÔNG thu hẹp phạm vi câu hỏi. Tuyến phòng thủ 2.
- **Lượt hỏi lại có tính vào `calls` trả về** để budget vẫn khớp với tiền đã tiêu.
- **Lưới cuối `_trim_to_last_sentence()`**: hỏi lại vẫn cắt → lùi về câu hoàn chỉnh cuối cùng.
  **Không** dán lời xin lỗi — câu trả lời phải đọc như một câu trả lời, không phải một thông báo lỗi.
- **Tách `_chat_once()`** khỏi `chat()` để vòng retry 429 dùng lại được cho cả hai lượt.

## Capabilities

### Modified Capabilities
- `chat-qa-service`: câu trả lời trả về client SHALL không bao giờ là văn bản dở dang; chạm trần output
  SHALL kích hoạt hỏi lại với ràng buộc độ dài thay vì trả về phần đã sinh kèm ghi chú.

## Non-goals

- **Không** thu hẹp phạm vi câu hỏi của người dùng — chỉ ép cách trình bày ngắn lại.
- **Không** streaming (đó là `chat-streaming-sse`); change này chỉ sửa đường blocking.
- **Không** đổi frontend, response shape, hay grounding.
- **Không** bỏ `_is_truncated()` — nó vẫn là tín hiệu kích hoạt.

## Dependencies

- `chatbot-qa` (archive 22/07/2026) — `GeminiClient.chat()` thuộc change đó.
- `gemini-structured-output` (archive 20/07/2026) — lý do chat không dùng `response_schema` vẫn giữ nguyên.

## Impact

- **Backend**: `ai/gemini_client.py` (`chat()` tách thành `chat()` + `_chat_once()`,
  `_CONCISE_RETRY_DIRECTIVE`, `_trim_to_last_sentence()`, `CHAT_MAX_OUTPUT_TOKENS`).
- **Chi phí**: chỉ tăng ở câu thực sự chạm trần (lượt hỏi lại thứ 2). Câu bình thường không đổi.
- **Budget**: một câu chạm trần tiêu 2 lượt — vẫn nằm trong `MAX_MODEL_CALLS_PER_QUESTION=2`.
- **Docs**: `CLAUDE.md` mục chat.
- **Không** đổi endpoint, không migration.
