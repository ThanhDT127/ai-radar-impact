# Proposal: chatbot-qa

**Phase áp dụng:** Phase 2 (M8 Chatbot/Search — điều kiện tiên quyết "insight repository đủ tốt" đã đạt với schema v2/v3).

> **Respec 22/07/2026.** Bản gốc viết 15/07 giả định một thế giới không còn tồn tại: bot transport
> Telegram (gỡ sạch 21/07 bởi `refactor-telegram-to-gmail-transport`), Vertex key chưa được cấp, và
> `response_schema` là cách chống bịa citation. Xem `design.md` mục "Đã đổi so với bản 15/07".

## Why

Insight đã được curate tốt nhưng người dùng chỉ tiêu thụ được theo kiểu đọc-lướt dashboard; không có
cách hỏi sâu ("cái này ảnh hưởng gì đến team tôi?", "tuần này có gì quan trọng cho Data/AI?") mà không
tự đọc từng bài. Chatbot Q&A grounded trên insight repository đóng đúng vai trò M8 trong architecture
vision.

Dữ liệu đo 22/07/2026 cho thấy repository đã đủ chín để làm nền: **179 insight** published+primary,
`signal`/`so_what` phủ **179/179**, `recommendations[role].urgency` phủ **179/179** (496 entry).

## What Changes

- **Chat service backend** với 2 chế độ trên cùng 1 endpoint `POST /api/v1/chat`
  (`question`, `history`, `insight_id?`):
  - **Chế độ B — per-insight** (`insight_id` có): context = insight fields + toàn bộ
    `raw_documents.normalized_content` của bài gốc. 1 lần gọi Gemini, ~$0.002/câu. Ship trước.
  - **Chế độ A — toàn cục** (`insight_id` null): **server** lọc cửa sổ thời gian → xếp hạng →
    dựng index nén → **1 lần gọi Gemini**. Không function-calling, không tool loop (xem `design.md` D3).
- **Grounding bằng cấu trúc, không bằng hậu kiểm**: server đánh số candidate `[n]` và giữ bảng
  `n → insight_id`; model chỉ trả **text thuần** có marker `[n]`. Model không bao giờ phát ra id, nên
  không có gì để bịa. Không tìm thấy thì trả lời "không tìm thấy trong hệ thống".
- **Web widget góc context-aware**: panel nổi (~380px, góc phải) trên mọi trang; khi đang mở insight
  detail thì tự gắn context chip (chế độ B), bấm ✕ chuyển hỏi toàn cục. Không thêm route mới.
- **Quota**: chat là consumer Gemini thứ hai — budget riêng `max_daily_chat_calls`, đếm trong bảng
  `chat_logs` (bảng log request cũng chính là counter). Analysis pipeline không bao giờ bị ăn budget.
- **History stateless**: web client tự gửi mảng history, cap 10 lượt. Không có bảng session.

## Capabilities

### New Capabilities
- `chat-qa-service`: endpoint chat 2 chế độ, retrieval server-driven, grounding + citation theo
  cấu trúc, budget riêng.
- `chat-web-widget`: widget góc context-aware trên React dashboard (context chip, 2 chế độ, render
  citation thành link).

### Modified Capabilities
_(không có — không đổi requirement của capability hiện hữu)_

### Đã bỏ khỏi change này
- ~~`chat-telegram-surface`~~ — transport Telegram không còn tồn tại (0 dòng trong `backend/app`).
  Người nhận nay định danh bằng email; email không mang được nút tương tác và hệ thống không có kênh
  inbound. Chat sống **chỉ trên dashboard**; email giữ đúng vai trò kênh push tin mức cao.

## Non-goals

- **Không** cầu nối từ email sang chat (deep-link `?ask=1`, inbound email Q&A). Quyết định 22/07:
  chat chỉ ở dashboard, email chỉ để gửi tin mức cao — hai kênh không cần dính nhau.
- **Không** function-calling / tool loop — đo trên corpus thật: nhét cả 179 insight dạng index nén
  vào 1 lần gọi tốn ~19.3k token (~$0.007/câu), rẻ hơn 2-3 lần và nhanh hơn 3-4 lần so với 2-4 lượt
  gọi tool. Để dành cho khi corpus vượt sức chứa của cửa sổ 90 ngày.
- **Không** vector DB / pgvector / semantic search.
- **Không** trang chat riêng (`/chat`) — chỉ widget.
- **Không** conversation store (threads, resume, share) — history stateless.
- **Không** streaming response.
- **Không** đổi provider AI, **không** nâng pin `google-genai==0.8.0` (pipeline analysis vừa được đo
  đạc kỹ ở `w4-gate-accuracy` và `gemini-structured-output`; đụng SDK là rủi ro lớn nhất không cần thiết).
- **Không** auth/user management mới.

## Dependencies

- **Vertex AI**: ~~chưa được cấp key~~ → **đã chạy thật** (benchmark gate 54 doc ngày 21/07, toàn bộ
  179 insight sinh bằng Vertex ngày 21/07). Không còn task nào bị chặn vì thiếu key.
- ~~`delivery-telegram`~~ — đã archive và đã bị thay thế; không còn là dependency.

## Impact

- **Backend**: mới `services/chat_service.py`, `routes/chat.py`, `schemas/chat.py`,
  `models/chat_log.py`, `repositories/chat_log_repo.py`, prompt chat trong `app/ai/prompts.py`;
  mở rộng `GeminiClient` (thêm `chat()`, giữ init) + **singleton client** cho request path;
  thêm filter `topics`/`published_since` vào `InsightRepository`; alembic `011` (bảng `chat_logs`).
- **Frontend**: component `ChatWidget` mới + `api/chat.ts`; mount ở `Layout.tsx`. Không đổi route,
  không đổi layout hiện có.
- **Config mới**: `max_daily_chat_calls`, `chat_window_days`.
- **Chi phí đo trên corpus thật**: chế độ B ~$0.002/câu, chế độ A ~$0.007/câu (toàn corpus 179 tin).
  Ở trạng thái ổn định 6 tháng (~1250 tin) chế độ A lên ~$0.042/câu, hạ về ~$0.021 nếu thu cửa sổ
  còn 90 ngày.
- **Nợ phát hiện khi respec, xử lý trong change này**: `CLAUDE.md` ghi sai `ALLOWED_TOPICS`
  (10 topic tiếng Việt cũ thay vì 12 topic v3 trong `prompts.py`).
