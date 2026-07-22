# Design: chatbot-qa

## Context

Insight repository đã đạt schema v2/v3 (`signal`, `why_it_matters`, `recommendations`, `so_what`, `urgency`, `affected_roles`…) — đủ giàu để làm nền cho Q&A grounded (điều kiện BRD "chatbot chỉ triển khai sau khi curated repository đủ tốt"). Hiện trạng liên quan:

- `GeminiClient` (`app/ai/gemini_client.py`) init Vertex tại đúng 1 chỗ; **giữ nguyên Vertex, đợi cấp key** — dev phần gọi AI bị chặn đến khi có key, các phần khác (endpoint, widget, tool layer) dev trước được với mock.
- Quota guard W1 (`max_daily_analysis`, rate-limit) hiện chỉ phục vụ analysis pipeline — chat là consumer Gemini thứ hai.
- Insights list API/repository đã có đủ filter: `role`, `urgency`, `momentum`, `vietnam_relevance`, `intelligence_tier`, `search`, pagination — tái dùng làm retrieval tool.
- `raw_documents.content` lưu full text bài gốc — mode B đọc trực tiếp, vượt qua giới hạn 6000 chars của analysis prompt.
- Frontend: 2 route (`/` split-view, `/insights/:id`), CSS Modules, TanStack Query; không có auth.

**Module ảnh hưởng:** M8 Chatbot/Search (chính), M5 Insight Repository (đọc), M7 Delivery (điểm nối nút inline), M10 Governance (quota, log). **Không liên quan n8n.**

## Goals / Non-Goals

**Goals:**
- Một chat service 2 chế độ (per-insight / toàn cục) trên 1 endpoint, grounded + citation bắt buộc.
- Widget web context-aware và Telegram Q&A dùng chung service.
- Chat không được làm analysis pipeline chết đói quota.
- Ship được theo pha: mode B trước (1 lần gọi, khó sai), mode A sau (function-calling).

**Non-Goals:**
- Vector search / pgvector; trang `/chat` riêng; conversation store (threads/resume); streaming response; đổi provider AI; Zalo; auth mới.

## Decisions

### D1. Một endpoint `POST /api/v1/chat`, `insight_id` optional — thay vì 2 endpoint riêng
Mode B là trường hợp con của mode A về pipeline trả lời (chỉ khác nguồn context). Chung endpoint → chung prompt scaffolding, chung quota check, UI chỉ đổi 1 param khi gắn/bỏ context chip. *Alternative bị loại:* `/chat/global` + `/chat/insight/{id}` — tách đôi codepath không đem lại gì ngoài trùng lặp.

**Request:** `{ question: str, history: [{role, content}], insight_id?: UUID }` — history stateless do client giữ (web) hoặc bảng session (Telegram), cap N=10 lượt gần nhất.
**Response:** `{ answer: str, citations: [{insight_id, title, source_url}], mode: "insight"|"global" }`.

### D2. Mode B: context = insight fields + full text bài gốc, 1 lần gọi Gemini
Nhét `title`, `signal`, `why_it_matters`, `recommendations`, `risks`, `summary_medium` + `raw_documents.content` (cap ~30.000 chars để giữ chi phí ~$0.004/câu) vào system context. Trả lời được cả chi tiết mà analysis đã cắt ở 6000 chars. *Alternative bị loại:* chỉ dùng insight fields — rẻ hơn chút nhưng bot không trả lời được gì sâu hơn cái card đã hiển thị, mất lý do tồn tại.

### D3. Mode A: Gemini function-calling với tool `search_insights` wrap repository hiện có
Tool declaration: `search_insights(keyword?, role?, topic?, urgency?, days_back?, limit<=10)` + `get_insight(insight_id)` — map thẳng vào `InsightRepository` (không qua HTTP nội bộ). Vòng lặp tool tối đa **4 lượt gọi model/câu hỏi**, vượt → trả lời với dữ liệu đã có. *Alternatives bị loại:* (a) pgvector semantic search — thêm hạ tầng + backfill embeddings trong khi câu hỏi thực tế đa phần là filter theo role/topic/thời gian; (b) nhét N insight gần nhất vào context — không trả lời được câu hỏi có điều kiện, tốn token vô ích.

### D4. Grounding strategy (model: Gemini 2.5 Flash qua Vertex AI, giữ nguyên)
- System prompt: chỉ được trả lời từ context/tool results; không có dữ liệu → nói rõ "không tìm thấy trong hệ thống"; **mọi khẳng định phải kèm citation** `[n]`; trả lời tiếng Việt.
- `temperature=0.2`, `response_mime_type=application/json` với schema `{answer, citation_ids}` — service resolve `citation_ids` → citations đầy đủ, loại id không tồn tại (chống bịa citation).
- Câu trả lời không có citation nào và không phải dạng "không tìm thấy" → service từ chối trả về, thay bằng thông báo không đủ căn cứ (fail-closed, ngược với gate analysis fail-open — chat sai còn tệ hơn chat thiếu).

### D5. Quota: mở rộng quota guard với budget riêng cho chat
Config mới `max_daily_chat_calls` (đếm mọi lượt gọi model, kể cả tool loop — mode A tính 2–4). Hết budget → HTTP 429 + message tiếng Việt lịch sự; **không bao giờ ăn vào budget analysis**. Đây là hàng rào cứng để buổi chiều team hỏi bot nhiều không giết pipeline ban đêm.

### D6. GeminiClient: thêm method `chat()`, không đổi init
Method mới nhận messages + tools + system prompt, giữ retry-429 pattern hiện có. Init Vertex nguyên trạng (quyết định đợi key, không thêm fallback API key trong change này).

### D7. Telegram session state: bảng `chat_sessions`
`(chat_id PK, context_insight_id UUID NULL, history JSONB, updated_at)` — đủ cho phiên mode B qua nút inline và history N lượt. Web không đụng bảng này (client tự giữ history). Migration Alembic 1 bảng.

### D8. Widget: component React thuần trong repo, không SDK ngoài
`ChatWidget` panel nổi ~380px góc phải, mount ở `Layout.tsx` (hiện trên mọi trang), CSS Modules như phần còn lại. Context chip lấy insight đang mở từ route param / state split-view. Gọi API bằng TanStack Query mutation. Không streaming v1 — câu trả lời ngắn (1 lần gọi mode B ~3-6s), spinner là đủ; streaming là nâng cấp sau nếu mode A chậm.

## Risks / Trade-offs

- [Hallucination/bịa citation] → JSON schema + resolve citation_ids server-side, loại id lạ; fail-closed khi không có citation (D4).
- [Tool loop chạy dài, đốt quota] → trần 4 lượt gọi/câu + đếm từng lượt vào budget (D3, D5).
- [Quota chat cạn giữa demo] → 429 có message rõ ràng; budget config được, tăng tạm khi demo.
- [Vertex key chưa có → không test được E2E] → dev theo pha: endpoint + tool layer + widget test với `GeminiClient` mock; khớp thật khi key về. Không workaround provider khác (quyết định đã chốt).
- [Latency mode A 2–4 lượt gọi tuần tự] → chấp nhận v1 (không streaming); hiển thị trạng thái "đang tìm trong hệ thống…" trên UI.
- [Widget che split-view trên màn hình hẹp] → panel toggle, không auto-mở, responsive thu gọn full-height trên mobile.
- [`chat-telegram-surface` phụ thuộc bot transport của `delivery-telegram`] → capability này implement sau cùng; service + widget không chờ.

## Open Questions

- Zalo có bắt buộc không (chờ mentor) — không chặn change này.
- Thời điểm được cấp Vertex key — quyết định mốc test E2E.
- Có cần lưu log câu hỏi/trả lời để đánh giá chất lượng (M9 Feedback) — đề xuất log tối thiểu (question, mode, citations count, latency) không lưu nội dung trả lời v1.
