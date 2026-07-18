# Tasks: chatbot-qa

> Thứ tự theo phase của design: nền tảng → chế độ B → widget → chế độ A → Telegram surface (cần bot transport từ `delivery-telegram`). Task 2.x–4.x dev được với GeminiClient mock trong khi chờ Vertex key; task đánh dấu **[cần key]** phải có key mới verify được.

## 1. Nền tảng backend

- [ ] 1.1 Migration Alembic: bảng `chat_sessions` (chat_id PK, context_insight_id UUID NULL, history JSONB, updated_at)
- [ ] 1.2 Config: thêm `max_daily_chat_calls` vào `config.py`; mở rộng quota guard đếm lượt gọi chat tách biệt budget analysis
- [ ] 1.3 Schemas Pydantic: `ChatRequest` (question, history, insight_id?), `ChatResponse` (answer, citations, mode)
- [ ] 1.4 `GeminiClient.chat()`: method nhận messages + system prompt + tools (optional), retry-429 theo pattern hiện có, `temperature=0.2`, JSON response schema `{answer, citation_ids}`

## 2. Chế độ B — per-insight

- [ ] 2.1 System prompt chế độ B: grounding rules (chỉ trả lời từ context, không tìm thấy thì nói rõ, citation bắt buộc, tiếng Việt) trong `app/ai/prompts.py`
- [ ] 2.2 `ChatService.answer_insight()`: load insight + `raw_documents.content` (cap 30.000 chars), build context, gọi Gemini 1 lượt
- [ ] 2.3 Resolve citations server-side: map citation_ids → DB, loại id không tồn tại; fail-closed khi không còn citation hợp lệ (trừ dạng "không tìm thấy")
- [ ] 2.4 Route `POST /api/v1/chat`: validate, 404 khi insight_id không tồn tại, 429 khi hết budget, error format chuẩn
- [ ] 2.5 Unit test service mode B với GeminiClient mock: happy path, insight_id sai, bịa citation, hết quota
- [ ] 2.6 **[cần key]** Test thủ công mode B với 10 câu hỏi thật trên insight có bài gốc dài (>6000 chars) — verify trả lời được chi tiết ngoài summary

## 3. Web widget

- [ ] 3.1 API client: `postChat()` trong `frontend/src/api/` + TanStack Query mutation
- [ ] 3.2 Component `ChatWidget`: nút góc phải dưới, panel ~380px, đóng/mở giữ hội thoại trong phiên, CSS Modules, mount ở `Layout.tsx`
- [ ] 3.3 Context chip: tự gắn theo insight đang mở (split-view + `/insights/:id`), ✕ để về chế độ toàn cục, cập nhật khi chuyển insight
- [ ] 3.4 Render trả lời: citations thành link mở insight detail; trạng thái loading; lỗi mạng cho gửi lại; message riêng cho 429
- [ ] 3.5 Responsive: panel full-height trên màn hình hẹp, không chặn thao tác nội dung chính trên desktop

## 4. Chế độ A — toàn cục (function-calling)

- [ ] 4.1 Tool declarations `search_insights(keyword?, role?, topic?, urgency?, days_back?, limit<=10)` + `get_insight(insight_id)` map vào `InsightRepository` (không qua HTTP)
- [ ] 4.2 `ChatService.answer_global()`: vòng lặp function-calling, trần 4 lượt gọi model, mỗi lượt đếm vào quota; chạm trần → ép trả lời với dữ liệu hiện có
- [ ] 4.3 System prompt chế độ A: khi tool trả rỗng phải trả lời "không tìm thấy trong hệ thống", cấm kiến thức ngoài
- [ ] 4.4 Unit test tool loop với mock: gọi tool đúng filter, chạm trần, tool rỗng → không bịa
- [ ] 4.5 **[cần key]** Test thủ công mode A: bộ 15 câu hỏi (theo role/topic/thời gian/keyword + 3 câu không có dữ liệu) — verify citation đúng và không bịa

## 5. Telegram surface (sau khi `delivery-telegram` có bot transport)

- [ ] 5.1 Message handler: text tự do từ chat đã `/start` → `ChatService.answer_global()`, format trả lời + citation links cho Telegram; chat lạ → hướng dẫn
- [ ] 5.2 Callback handler nút "Hỏi về tin này": set `chat_sessions.context_insight_id`, xác nhận với người dùng; câu hỏi sau đó → `answer_insight()`
- [ ] 5.3 Lệnh `/reset`: xóa context, xác nhận; bấm nút tin khác → chuyển context
- [ ] 5.4 History per-chat: lưu/cắt 10 lượt gần nhất trong `chat_sessions`, gửi kèm khi gọi service
- [ ] 5.5 Message 429 tiếng Việt khi hết budget
- [ ] 5.6 **[cần key]** Test E2E trên Telegram thật: push tin → bấm nút → hỏi 3 câu nối tiếp → `/reset` → hỏi toàn cục

## 6. Hoàn tất

- [ ] 6.1 Log tối thiểu mỗi request chat: mode, số lượt gọi model, citations count, latency (không lưu nội dung trả lời)
- [ ] 6.2 Cập nhật CLAUDE.md (endpoint chat, budget config) + `docs/system_overview.md`
- [ ] 6.3 `openspec validate` + verify spec scenarios trước khi archive
