# Design: chat-answer-completeness

## Context

`GeminiClient.chat()` trả `(text, calls)`. Khi `finish_reason == MAX_TOKENS`, nó nối thêm một dòng
markdown xin lỗi vào cuối `text` rồi trả về như thường. Không có nhánh nào cố lấy lại nội dung đã mất.

Chỗ này dễ chạm trần hơn vẻ ngoài: Gemini 2.5 tiêu **thinking tokens trong cùng ngân sách output**
(đo thật 121→3.791 token/câu), nên trần 4096 không phải là "4096 token văn bản".

**Module ảnh hưởng:** M8 (Chatbot) — thuần backend, một file.
**API endpoints:** `POST /api/v1/chat` — không đổi shape.
**Bảng DB:** không đụng, không migration.

## Goals / Non-Goals

**Goals:**
- Client không bao giờ nhận văn bản đứt giữa từ.
- Giữ **đủ ý** khi phải rút ngắn — rút gọn cách trình bày, không rút gọn phạm vi trả lời.
- Budget vẫn khớp với số lượt thực sự tốn tiền.

**Non-Goals:**
- Không xử lý cắt dưới chế độ streaming (thuộc `chat-streaming-sse`).
- Không đặt mục tiêu 0% chạm trần — chỉ đảm bảo chạm trần không lộ ra ngoài.

## Decisions

### D1: Ba tuyến phòng thủ theo thứ tự rẻ → đắt

1. **Trần cao hơn (4096 → 8192)** — 0 chi phí thêm. Vertex tính tiền theo token **thực sinh**, nên trần
   cao không làm câu ngắn đắt hơn; nó chỉ ngừng cắt oan câu dài. Phải thử cái này trước khi nghĩ tới
   việc gọi lại model.
2. **Hỏi lại có ràng buộc độ dài** — tốn 1 lượt, chỉ với câu thực sự chạm trần.
3. **Lùi về ranh giới câu** — 0 chi phí, chỉ là lưới an toàn.

**Vì sao không đảo thứ tự:** nếu chỉ nâng trần mà không có tuyến 2 thì vẫn có câu chạm 8192; nếu chỉ hỏi
lại mà không nâng trần thì trả tiền cho lượt thứ hai ở những câu lẽ ra vừa đủ chỗ.

### D2: Ràng buộc *độ dài trình bày*, không phải *phạm vi trả lời*

`_CONCISE_RETRY_DIRECTIVE` yêu cầu "gộp các tin tương tự vào một gạch", "bỏ phần dẫn nhập", "tối đa 5
gạch đầu dòng" — và nói rõ **"phủ ĐỦ Ý đã hỏi"**.

**Vì sao:** yêu cầu Hung là "ngắn gọn **nhưng đủ ý**". Bảo model "chỉ trả lời 3 tin đầu" sẽ tái lập đúng
lỗi đang sửa — vẫn là câu trả lời thiếu, chỉ khác là thiếu một cách gọn gàng hơn. Câu hỏi của người dùng
được truyền lại **nguyên văn**; chỉ `system_instruction` được nối thêm.

### D3: Hỏi lại đúng MỘT lần

**Vì sao:** mỗi lượt là 5–22,6s. Leo thang nhiều bậc ("rất ngắn gọn", "cực ngắn") sẽ biến một câu hỏi
thành cả phút chờ để cứu một ca hiếm. Một lần + lưới an toàn là đủ; nó cũng vừa khít
`MAX_MODEL_CALLS_PER_QUESTION=2` đã có sẵn.

### D4: Lưới cuối cắt về câu, KHÔNG dán ghi chú

**Chọn:** `_trim_to_last_sentence()` cắt tại `.!?…` cuối cùng; không tìm thấy ranh giới nào thì trả
nguyên văn (cắt bừa còn tệ hơn).

**Vì sao không dán ghi chú:** đó chính là hành vi đang bị bác bỏ. Một câu trả lời ngắn hơn mà **đọc trọn
vẹn** thì trung thực hơn một câu trả lời dài kèm lời thú nhận nó không dùng được.

**Đánh đổi:** có thể mất ý cuối mà không báo. Chấp nhận vì đây là nhánh thứ ba (đã qua trần 8192 **và**
một lượt ép gộp ý) — xác suất tới đây rất thấp, và log warning vẫn ghi lại.

### D5: Tách `_chat_once()`

Vòng retry 429 (delay 3s/10s) phải áp dụng cho **cả** lượt đầu và lượt hỏi lại. Tách hàm là cách rẻ nhất
để không nhân đôi logic đó. `_chat_once()` trả `(text, bị_cắt, calls)` — trả cờ cắt ra ngoài thay vì
giấu trong text để `chat()` quyết định.

### D6: Lượt hỏi lại có tính vào `calls`

**Vì sao:** `calls` là "số lượt ĐÃ TỐN TIỀN", `ChatService._call_model()` cộng thẳng vào `_calls_used`.
Không đếm lượt hỏi lại là rò rỉ budget — đúng cái bẫy mà comment trong `chat_service.py` đã cảnh báo.

## Risks / Trade-offs

- **Câu chạm trần nay chậm gấp đôi** (2 lượt). Chấp nhận: thà chờ lâu hơn và nhận câu trả lời dùng được.
- **Trần 8192 làm câu lan man tốn hơn** nếu model thực sự sinh dài. Bù lại là bớt lượt hỏi lại.
- **`_trim_to_last_sentence` có thể cắt nhầm** ở dấu chấm trong "vd.", "v.v.". Ảnh hưởng nhỏ và chỉ ở
  nhánh hiếm nhất.

## Open Questions

- Có nên đếm tần suất chạm trần để biết trần 8192 đã đủ chưa? Hiện chỉ có `logger.warning`. Chờ dữ liệu
  thật thay vì thêm cột ngay.
