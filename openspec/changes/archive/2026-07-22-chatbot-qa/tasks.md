# Tasks: chatbot-qa

> Respec 22/07/2026. Thứ tự theo phase: nền tảng → chế độ B → widget → chế độ A → hoàn tất.
> Vertex đã chạy thật nên **không còn task nào bị chặn vì thiếu key**.
> Section Telegram (6 task) và migration `chat_sessions` đã bị xoá — transport không còn tồn tại.

## 1. Nền tảng backend

- [x] 1.1 Migration Alembic `011`: bảng `chat_logs` (`id` UUID PK, `mode` VARCHAR(10), `model_calls` INT, `citations_count` INT, `latency_ms` INT, `created_at` TIMESTAMP mặc định `now()`), index trên `created_at`. **DoD:** `alembic upgrade head` → `downgrade -1` → upgrade lại, cả hai chiều chạy sạch.
- [x] 1.2 Config: thêm `max_daily_chat_calls: int = 200` và `chat_window_days: int = 0` vào `config.py` + `.env.example`. Comment ghi rõ **đơn vị đo lệch nhau**: `max_daily_analysis` đếm *tài liệu* (1 tài liệu = 2 lượt gọi model), `max_daily_chat_calls` đếm *lượt gọi*.
- [x] 1.3 `models/chat_log.py` + `repositories/chat_log_repo.py`: `create()` và `sum_model_calls_today()` (đếm theo **UTC**, khớp `count_analyzed_today`). **DoD:** unit test cho ranh giới nửa đêm UTC.
- [x] 1.4 Schemas Pydantic (`schemas/chat.py`): `ChatRequest` (question, history cap 10, insight_id?), `ChatResponse` (answer, citations, mode), `Citation` (insight_id, title, source_url).
- [x] 1.5 `GeminiClient.chat()`: nhận system prompt + messages, `temperature=0.2`, `max_output_tokens=2048`, **KHÔNG** `response_mime_type`/`response_schema`, giữ retry-429 theo pattern hiện có; trả `(text, model_calls_used)`.
- [x] 1.6 Singleton client cho request path (module-level hoặc `app.state`) — **KHÔNG** khởi tạo `GeminiClient()` trong `Depends(...)`. **DoD:** log/assert xác nhận 2 request liên tiếp dùng cùng một instance.
- [x] 1.7 `InsightRepository.list_for_chat(published_since, topics=None, roles=None, keyword=None)` — luôn `status="published" AND is_primary=True`. **KHÔNG** sửa `list_paginated` (hàm đó phục vụ UI). **DoD:** test khẳng định điều kiện `is_primary` có mặt, theo tiền lệ `tests/test_insight_count_queries.py`.

## 2. Grounding + chế độ B

- [x] 2.1 System prompt chat trong `app/ai/prompts.py`: chỉ trả lời từ context; không có dữ liệu → nói rõ "không tìm thấy trong hệ thống"; mọi khẳng định phải kèm marker `[n]`; trả lời tiếng Việt (technical terms giữ tiếng Anh).
- [x] 2.2 Lớp citation: server đánh số candidate `[1..N]`, giữ bảng `n → insight_id`, **không đưa UUID vào prompt**; parse marker trong câu trả lời → dựng `citations`; marker ngoài phạm vi → bỏ marker, **giữ** phần còn lại của answer.
- [x] 2.3 Fail-closed: answer mang tính khẳng định mà không có marker nào → thay bằng thông báo không đủ căn cứ. Answer dạng "không tìm thấy" đi qua với `citations=[]`.
- [x] 2.4 `ChatService.answer_insight()`: load insight + `raw_documents.normalized_content` (**không cắt** — trần 8000 ký tự đã áp từ ingest), build context, gọi Gemini 1 lượt qua `asyncio.to_thread`.
- [x] 2.5 Fallback khi `normalized_content` rỗng/NULL (tombstone-purge): chạy bằng insight fields + nói rõ "bài gốc đã hết hạn lưu trữ".
- [x] 2.6 Route `POST /api/v1/chat` + đăng ký vào `main.py`: validate, 404 khi `insight_id` không tồn tại (**không gọi Gemini**), 429 khi hết budget, error format chuẩn.
- [x] 2.7 Ghi `chat_logs` trong khối `finally` — call đã trả về rồi vỡ ở bước sau **vẫn phải tính**; retry 429 (không có response) không tính.
- [x] 2.8 Unit test service mode B với `GeminiClient` mock: happy path, `insight_id` sai, marker ngoài phạm vi, answer không marker → fail-closed, content rỗng → fallback, hết quota → 429.
- [x] 2.9 Test thủ công mode B với Vertex thật: 10 câu hỏi trên insight có bài gốc >6000 ký tự. **DoD:** trả lời được chi tiết nằm ngoài `summary_medium`, 10/10 có citation đúng insight đang hỏi.

## 3. Web widget

- [x] 3.1 API client: `postChat()` trong `frontend/src/api/chat.ts` + TanStack Query mutation + type trong `types/`.
- [x] 3.2 Component `ChatWidget`: nút góc phải dưới, panel ~380px, đóng/mở giữ hội thoại trong phiên, CSS Modules, mount ở `Layout.tsx`. Không tự động mở.
- [x] 3.3 Context chip: tự gắn theo `/insights/:id`, ✕ để về chế độ toàn cục, cập nhật khi chuyển insight, **biến mất khi rời trang chi tiết**.
- [x] 3.4 Render trả lời: marker `[n]` thành link mở `/insights/:id`; trạng thái loading; lỗi mạng cho gửi lại; message riêng cho 429.
- [x] 3.5 Gửi tối đa 10 lượt history gần nhất kèm mỗi request.
- [x] 3.6 Responsive: panel full-height trên màn hình hẹp, không chặn thao tác nội dung chính trên desktop.
- [x] 3.7 **Nợ kỹ thuật — vá sau khi Hung xem màn hình thật (22/07).** Section 3 từng bị đánh dấu xong khi mới có "compile sạch + module load", chưa ai nhìn bằng mắt. Ảnh chụp thật lộ ra: panel **tràn ngang, sinh thanh cuộn** vì marker `[n]` inline dùng chung class với danh sách nguồn (`white-space: nowrap` + flex `min-width: auto` → đẩy rộng cả panel thay vì bị cắt). Đã vá: tách `.marker` khỏi `.citationLink`, `overflow-x: hidden` chốt chặn, `overflow-wrap: anywhere`. Kèm theo yêu cầu của Hung: rộng 380→`min(520px, 100vw−48px)`, chiều cao **cố định** 600px thay vì co giãn theo số tin nhắn. **Bài học: "tsc pass" không phải bằng chứng UI dùng được.**

## 4. Chế độ A — toàn cục

- [x] 4.1 Builder index nén: `[n] | title | signal | roles | topics | ngày` (~108 token/dòng). **DoD:** đo token thật của index trên corpus hiện tại, đối chiếu ước tính 19.3k cho 179 tin; lệch >30% thì xem lại kích thước dòng. ✅ Đo thật: 179 tin → index 62.969 ký tự → **19.126 token** (ước tính 19,3k, **lệch 1%**).
- [x] 4.2 `ChatService.answer_global()`: `list_for_chat` theo `chat_window_days` → xếp hạng bằng `delivery_engine.score_for_role()` (**gọi lại, không viết lại**) → dựng index → 1 lượt gọi. Trần cứng **2 lượt gọi/câu hỏi**.
- [x] 4.3 Vai trò không có dữ liệu (Data Analyst, Người dùng phổ thông — 0 entry ở thời điểm respec) → trả lời rõ "chưa có tin nào cho vai trò này".
- [x] 4.4 Unit test mode A với mock: index chứa đúng candidate đã lọc/xếp hạng, không rò UUID vào prompt, index rỗng → "không tìm thấy" chứ không bịa, vai trò 0 dữ liệu.
- [x] 4.5 Test thủ công mode A với Vertex thật: 15 câu hỏi (theo vai trò / topic / thời gian / keyword + 3 câu chắc chắn không có dữ liệu). **DoD:** citation trỏ đúng insight, 3 câu không dữ liệu đều trả "không tìm thấy", 0 câu bịa nội dung ngoài index. ✅ 15/15 đạt: Q13-Q15 (ngoài corpus) + Q10 (vai trò 0 dữ liệu) đều trả "không tìm thấy" với 0 citation. **Phát hiện + đã vá:** model ban đầu đổ gần hết index thành danh sách (Q3 = 92 citation, 19,6s) → thêm luật trần 5 tin + dòng "Còn N tin khác" vào prompt; sau vá còn 3-5 citation, câu trả lời trọn vẹn.
- [x] 4.6 Đo chi phí + độ trễ thật trên 15 câu ở 4.5. **DoD:** ghi số đo vào change (ước tính $0.007/câu, ~3-6s); lệch lớn thì ghi rõ nguyên nhân. ✅ Đo n=3: **$0,006-0,016/câu** (tb ~$0,011), **5,0-22,6s** (15 câu qua HTTP: tb 9,7s). **Nguyên nhân lệch: thinking tokens** (121→3.791 tok/câu) bị tính tiền như output, design không tính tới. Bảng số đo + phân tích ở `design.md` D3.

## 4b. Tối ưu chi phí (thêm 22/07 sau khi đo)

- [x] 4b.1 `chat_index_top_k` (60) — cắt index sau xếp hạng. **DoD:** đo A/B cùng câu hỏi. ✅ top-179 → top-60: 19.126→6.670 input, 3.930→2.534 thinking, 23,0→15,0s, $0,0160→$0,0090 (**−44% chi phí, −35% thời gian**).
- [x] 4b.2 Xếp hạng hai tầng: độ liên quan câu hỏi → `score_for_role`. **DoD:** đo recall tin liên quan bằng từ khoá độc lập với bảng xếp hạng. ✅ **42% → 91%**. Không có tầng này thì top-K cắt sạch tin đúng chủ đề nhưng urgency thấp ("mã nguồn mở" chỉ còn 2/18 tin) — và **im lặng**, bộ 15 câu vẫn "đạt" vì model trả lời trôi chảy từ phần sót.
- [x] 4b.3 Ngưỡng tách từ 2 ký tự (tiếng Việt đơn âm). **DoD:** "mã nguồn mở" phải giữ đủ từ khoá. ✅ `['mô','hình','mã','nguồn','mở']` thay vì `['nguồn']`; ca này 94%→100%, tổng recall giữ 91%.
- [x] 4b.4 `empty_roles` tính TRƯỚC khi cắt top-K + test hồi quy. **DoD:** vai trò có tin xếp dưới ngưỡng không bị báo nhầm "chưa có tin nào".
- [x] 4b.5 Test hồi quy cho 4b.1-4b.4 (6 test mới trong `test_chat_mode_global.py`).

## 5. Hoàn tất

- [x] 5.1 Kiểm tải nhẹ: bắn 5 câu hỏi đồng thời, xác nhận API khác (`/insights`, `/insights/stats`) vẫn phản hồi bình thường — chứng minh không chặn event loop. ✅ 5 chat song song: `/insights/stats` 17-82ms, `/insights?size=20` 57-116ms — ngang lúc nhàn rỗi (18ms).
- [x] 5.2 Rà tay 20 câu trả lời tìm nội dung không có căn cứ trong index/context. **DoD:** ghi lại số ca sai; >2/20 thì siết prompt trước khi archive. ✅ Rà 25 câu (15 mode A + 10 mode B), spot-check 5 khẳng định cụ thể với DB (signal Voicebox, risks + affected_roles của Security Hub, signal Fortinet/CISA, signal TP-Link Kasa) — **khớp nguyên văn, 0 ca bịa**. 4 câu ngoài corpus đều trả "không tìm thấy".
- [x] 5.3 Sửa `CLAUDE.md`: cập nhật `ALLOWED_TOPICS` sai (10 topic tiếng Việt cũ → 12 topic v3 trong `prompts.py`); thêm mục endpoint chat + `max_daily_chat_calls`/`chat_window_days` + ghi chú đơn vị đo quota; cập nhật `docs/system_overview.md`.
- [x] 5.4 `openspec validate chatbot-qa --strict` + đối chiếu từng scenario trong specs trước khi archive. ✅ validate PASS, 139 test pass, frontend build sạch. **Còn treo: chưa xác minh widget bằng mắt trên trình duyệt** (mới compile + load module).
