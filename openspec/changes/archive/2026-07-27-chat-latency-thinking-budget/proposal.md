# Proposal: chat-latency-thinking-budget

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — độ trễ trả lời).

## Why

Chat trả lời **14,6–29,1s** cho câu tra cứu thật. Đo 27/07/2026 tìm ra nguyên nhân, và nó
**không phải** retrieval: model tiêu **1.877–2.752 token thinking** mỗi câu trong khi câu trả
lời chỉ **233–282 token** — gấp ~10 lần. Bằng chứng sạch nhất: prompt tầm thường (534 token
vào, 10 token ra, "trả lời đúng một từ") vẫn mất **10,3s** vì vẫn nghĩ 1.416 token.

Chi phí này **vô hình từ trước tới nay**: `google-genai==0.8.0` không phơi
`thoughts_token_count` (luôn trả `0`/`None`), phải suy ra từ chỗ lệch của `total_token_count`
so với vào+ra. Nó cũng không có `thinking_budget` — chỉ có `ThinkingConfig(include_thoughts)`
— nên không có cách nào ghìm lại ở bản đang pin.

Đo trên **đúng prompt chat thật** với SDK 2.x: hiện tại 8,2s / 1.023 thinking →
`thinking_budget=256` còn **3,7s / 253 thinking**, câu trả lời và citation giữ nguyên chất
lượng (vẫn nêu đủ HiveLegacy 0-day, CISA/Fortinet, 5 marker hợp lệ). `budget=0` còn 1,8s.

## What Changes

- **Nâng `google-genai` 0.8.0 → 2.x.** Bản pin cũ vừa thiếu `thinking_budget` vừa giấu
  `thoughts_token_count` — hai thứ cần để *ghìm* và để *nhìn thấy* chi phí này.
- **`thinking_budget = 256` CHỈ cho đường chat** (`GeminiClient.chat()` +
  `chat_stream()`). Chọn 256 chứ không 0: giữ một biên suy luận cho câu tổng hợp, đổi lấy
  ~1,9s so với 0. Thành hằng số cấu hình được (`CHAT_THINKING_BUDGET`) vì nó là **núm điều
  chỉnh đánh đổi tốc độ ↔ chất lượng**, và cổng chất lượng mới là thứ quyết giá trị của nó.
- **`gate_analyze` / `analyze` / `classify_intent` GIỮ NGUYÊN hành vi.** Chúng là batch job,
  độ trễ không quan trọng; đụng vào là phải chạy lại benchmark gate 54 doc và chấp nhận rủi ro
  accuracy 94% / recall 100% tụt — không đáng cho mục tiêu này.
- **Embed câu hỏi chạy song song với truy vấn DB.** Hiện tuần tự (DB ~0,2s rồi embed ~1,4s);
  hai việc độc lập nhau nên `asyncio.gather` cắt được ~0,2s.
- **Ghi `thoughts_token_count` vào log chat.** Để chi phí thinking không bao giờ vô hình lại.

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-qa-service`: hệ thống SHALL ghìm ngân sách suy luận của lượt sinh câu trả lời chat và
  SHALL đo được số token suy luận đã dùng; hai bước chuẩn bị ngữ cảnh độc lập SHALL chạy song song.

## Non-goals

- **Không** cắt `CHAT_INDEX_TOP_K`. Đo được: 60 → 10 (giảm 76% token vào) chỉ đưa 17,4s xuống
  11,6s, mà trả bằng recall — sai đường.
- **Không** đụng `_rank`/retrieval (vừa land ở `chat-hybrid-retrieval`), không đụng grounding,
  citation, fail-closed, scope routing, streaming.
- **Không** đổi model (`gemini-2.5-flash` giữ nguyên), không đổi `thinking_budget` của gate/analysis.
- **Không** hạ ngưỡng eval để lấy tốc độ. Faith < 0,95 hoặc CitPrec < 1,00 ⇒ **nâng budget**
  256 → 512, không hạ ngưỡng.

## Dependencies

- `chat-hybrid-retrieval` (⑥) — cứng, land trước: nó vừa sửa `_rank` và vừa chốt lại cả hai
  baseline; change này phải đo trên nền đó.
- `chat-streaming-sse` (⑤) — `chat_stream()` cũng phải nhận `thinking_budget`, không thì hai
  lối ra có hành vi khác nhau (đúng cái bẫy "đừng tách hai nhánh logic").
- `chat-eval-quality-gate` (④) — là **cổng bắt buộc** của change này.

## Impact

- **Dependency**: `backend/requirements.txt` — `google-genai` 0.8.0 → 2.x. Đây là API surface
  dùng chung của gate/analyze/chat/stream/intent/embed ⇒ toàn bộ suite phải xanh lại.
- **Backend**: `ai/gemini_client.py` (thinking config + đọc `thoughts_token_count`),
  `services/chat_service.py` (gather embed ‖ DB, log token suy luận), `config.py`
  (`chat_thinking_budget`), `models/chat_log.py` + migration nếu lưu token suy luận.
- **Test/Eval**: `chat_answer_harness --live` là cổng cứng (Faith ≥ 0,95, CitPrec = 1,00);
  RS harness phải **không đổi** (không đụng `_rank`) — nếu đổi là dấu hiệu chạm nhầm chỗ.
- **Docs**: `CLAUDE.md` — nguyên nhân độ trễ thật, vì sao KHÔNG cắt top-K, núm `thinking_budget`.
