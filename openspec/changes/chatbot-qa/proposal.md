# Proposal: chatbot-qa

**Phase áp dụng:** Phase 2 (M8 Chatbot/Search — điều kiện tiên quyết "insight repository đủ tốt" đã đạt với schema v2/v3).

## Why

Insight đã được curate tốt nhưng người dùng chỉ tiêu thụ được theo kiểu đọc-lướt dashboard; không có cách hỏi sâu ("cái này ảnh hưởng gì đến team tôi?", "tuần này có gì quan trọng cho Data/AI?") mà không tự đọc từng bài. Chatbot Q&A grounded trên insight repository đóng đúng vai trò M8 trong architecture vision và là yêu cầu trực tiếp từ task hiện tại.

## What Changes

- **Chat service backend** với 2 chế độ trên cùng 1 endpoint `POST /api/v1/chat` (`question`, `history`, `insight_id?`):
  - **Chế độ B — per-insight** (`insight_id` có): context = insight fields + full text bài gốc từ `raw_documents` (không bị giới hạn 6000 chars như analysis prompt), 1 lần gọi Gemini. Ship trước.
  - **Chế độ A — toàn cục** (`insight_id` null): Gemini function-calling với tool `search_insights` wrap repository/filter hiện có (role, topic, urgency, keyword, thời gian), 2–4 lượt gọi/câu hỏi. Bật sau, không đổi endpoint/UI.
- **Grounding bắt buộc**: trả lời kèm citation (id/url insight nguồn); không tìm thấy thì trả lời "không tìm thấy", cấm suy diễn ngoài dữ liệu.
- **Web widget góc context-aware**: panel nổi (~380px, góc phải) trên mọi trang; khi đang mở insight detail thì tự gắn context chip (chế độ B), bấm ✕ chuyển hỏi toàn cục. Không thêm route mới, không đụng layout split-view.
- **Telegram Q&A surface**: nhắn với bot = hỏi toàn cục; bấm nút inline "Hỏi về tin này" trên tin push = vào phiên chế độ B (state `chat_id → insight_id`, `/reset` để thoát). Dùng chung bot transport do change `delivery-telegram` cung cấp.
- **Quota**: chat là consumer Gemini thứ hai — tích hợp quota guard (W1) với budget riêng cho chat; analysis pipeline được ưu tiên trước.
- **History stateless v1**: web client tự gửi mảng history; Telegram lưu N tin gần nhất mỗi chat trong 1 bảng nhỏ.

## Capabilities

### New Capabilities
- `chat-qa-service`: endpoint chat 2 chế độ, retrieval qua function-calling, grounding + citation, tích hợp quota guard.
- `chat-web-widget`: widget góc context-aware trên React dashboard (context chip, 2 chế độ, render citation thành link).
- `chat-telegram-surface`: Q&A qua Telegram bot — message handler, phiên context per-insight qua nút inline, `/reset`.

### Modified Capabilities
_(không có — không đổi requirement của capability hiện hữu)_

## Non-goals

- **Không** vector DB / pgvector / semantic search — retrieval v1 dùng structured filter + keyword qua repository hiện có; pgvector để dành khi Q&A đòi semantic thật sự.
- **Không** trang chat riêng (`/chat`) — chỉ widget; trang riêng là việc thuần UI về sau nếu cần hội thoại kiểu nghiên cứu.
- **Không** conversation store xịn (threads, resume, share) — history stateless v1.
- **Không** đổi provider AI: giữ Vertex AI (`GeminiClient`) nguyên trạng, đợi cấp key. Không thêm DeepSeek fallback trong change này.
- **Không** Zalo — chờ xác nhận mentor (cần OA doanh nghiệp + webhook public).
- **Không** auth/user management mới — widget dùng session hiện có của dashboard; Telegram định danh bằng `chat_id`.

## Dependencies

- **`delivery-telegram`**: cung cấp bot transport (long-polling worker, channel adapter) và nút inline trên tin push. `chat-qa-service` + `chat-web-widget` triển khai độc lập được; riêng `chat-telegram-surface` cần bot transport từ change kia.
- **Quota guard W1**: mở rộng budget cho chat.
- **Vertex AI key**: chưa được cấp — dev/test bị chặn cho đến khi có key (quyết định giữ nguyên, không workaround).

## Impact

- **Backend**: mới `services/chat_service.py`, `routes/chat.py`, tool declarations cho Gemini function-calling; mở rộng `GeminiClient` (thêm method chat/function-calling, không đổi init); bảng nhỏ lưu Telegram chat history/context.
- **Frontend**: component `ChatWidget` mới + state context chip; không đổi route, không đổi layout hiện có.
- **Chi phí**: chế độ B ~$0.004/câu, chế độ A ~$0.015–0.025/câu (đã ước tính); quota guard phải chặn chat trước khi chạm budget analysis.
