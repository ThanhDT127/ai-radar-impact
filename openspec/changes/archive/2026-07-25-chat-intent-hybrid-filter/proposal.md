# Proposal: chat-intent-hybrid-filter

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot). Sửa trực tiếp bộ định tuyến vừa ship ở `chat-intent-router`.

## Why

Bộ phân loại tất định ship ngày 24/07 đo lại ngày 25/07 trên **70 ca nhãn tay**: precision 100% nhưng
recall chỉ **73,7%** — 10/38 câu chào/meta lọt lưới. Nguyên nhân cấu trúc: cổng "phần còn lại rỗng" chạy
**trước** phần khớp cụm năng lực, nên **14/17 cụm trong `_CAPABILITY_PHRASES` là code chết** — cụm nào chứa
từ ngoài `STOPWORDS`/filler ("giúp", "chức năng", "hoạt động", "giới thiệu") không bao giờ được so tới.

Hung yêu cầu (25/07) thay matching bằng một model nhẹ trên Vertex làm bộ lọc đầu vào, **ưu tiên độ trễ thấp
nhất**. Đo thật trước khi ráp cho thấy giao hết cho model là sai hướng:

- Sàn round-trip `gemini-2.5-flash-lite` = **1.433–1.685 ms** *kể cả prompt rỗng + 1 token output*. Đó là
  mạng + TTFT, **không cắt được** bằng cách chọn model nhỏ hơn.
- Giao hết cho model = cộng ~1,45s vào **mọi** câu, kể cả câu tra cứu thật (15,9s → 17,4s).
- Precision của model trên chính tập đó chỉ **91,5%**, *thấp hơn* 97,6% của luật — nó gạt nhầm
  "cảm ơn vì tin về mã nguồn mở" thành `thanks`.

Luật thắng ở ca rõ ràng, model thắng ở ca mập mờ. Hung chốt phương án **lai**.

## What Changes

- **Tầng 1 `route_intent()` trả ba trạng thái** — nhóm preset / `None` (câu tra cứu) / `AMBIGUOUS`. Quyết
  **96,4%** số câu ở 6µs, 0 đồng.
- **Tầng 2 `GeminiClient.classify_intent()`** — `gemini-2.5-flash-lite`, **chỉ** chạy khi tầng 1 tự nhận
  lưỡng lự (**3,6%** câu). Nhãn một ký tự, `max_output_tokens=4`, `temperature=0`, **không retry**.
- **Luật đại từ hồi chỉ** (`_ANAPHORA_TOKENS`): "nó"/"này"/"cái"/"bài" không kèm tự-quy-chiếu
  (`bạn`/`bot`/`trợ lý`) ⇒ câu tra cứu. Đây là ca **cả matching cũ lẫn flash-lite đều sai**.
- **`_CAPABILITY_CONTENT_TOKENS` suy ra tự động** từ `_CAPABILITY_PHRASES` — để lỗi "cụm chết" không tái sinh.
- **Lượt gọi tầng 2 KHÔNG tính vào `model_calls`** — bộ đếm đó canh budget lượt trả lời đắt.
- **Tắt được bằng `INTENT_CLASSIFIER_ENABLED=false`** → lưỡng lự rơi về pipeline (giữ bias fall-through).

Kết quả đo bộ lai trên 84 ca: **precision 100%, recall 97,7%, đúng hoàn toàn 98,8%**.

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-qa-service`: định tuyến ý định SHALL là hai tầng — luật tất định quyết ca rõ ràng, model nhẹ chỉ
  phán ca luật tự nhận lưỡng lự. Bỏ ràng buộc "SHALL KHÔNG dùng model để phân loại ý định" của
  `chat-intent-router`.

## Non-goals

- **Không** giao toàn bộ phân loại cho model — đo được là chậm hơn *và* kém chính xác hơn.
- **Không** retry tầng 2: retry ở đây cộng thẳng vài giây vào thời gian người dùng chờ để cứu một phân
  loại mà fallback đã xử lý đúng.
- **Không** đổi preset, `mode="meta"`, hay hành vi quota của fast-path.
- **Không** đổi frontend, không migration.

## Dependencies

- `chat-intent-router` (archive 25/07/2026) — change này sửa trực tiếp yêu cầu do nó tạo ra.

## Impact

- **Backend**: `services/chat_intent.py` (`route_intent`, `AMBIGUOUS`, `_ANAPHORA_TOKENS`,
  `_SELF_TOKENS`, `_CAPABILITY_CONTENT_TOKENS` suy tự động), `ai/gemini_client.py`
  (`classify_intent()`, `INTENT_CLASSIFIER_PROMPT`, `INTENT_LABELS`), `services/chat_service.py`
  (`_route_intent()`), `config.py` (2 setting mới).
- **Chi phí**: ≈ $0,026/1000 câu hỏi (chỉ 3,6% câu chạm model).
- **Docs**: `CLAUDE.md` — sửa dòng "ĐỪNG đổi sang LLM classifier" nay đã sai.
- **Không** đổi endpoint, không migration.
