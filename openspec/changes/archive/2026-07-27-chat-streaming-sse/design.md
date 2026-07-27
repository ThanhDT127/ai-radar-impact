## Context

Báo cáo To‑Be mục 3.2 #3 giải Nguy hiểm #1 bằng **SSE streaming + Agent Progress Status**: trả token ngay,
giảm perceived latency, và phát trạng thái suy luận trong lúc chờ. Hiện `POST /api/v1/chat` blocking, độ trễ
thật 5–22,6s (thinking‑heavy), widget một spinner. `chat-scope-routing` (③) đẩy lên 10–45s cho câu mở rộng.
Reformulator đã hoãn tới khi có ⑤ (chốt ②).

**Module ảnh hưởng:** M8 (Chatbot/Search) — backend (client + service + route) + frontend (widget).
**API endpoints:** **thêm** `POST /api/v1/chat/stream` (SSE, `text/event-stream`). `POST /api/v1/chat`
blocking **giữ nguyên**. Không xoá/đổi endpoint cũ.
**Bảng DB:** không đụng, không migration.
**AI/LLM:** Gemini 2.5 Flash qua Vertex — dùng API **sinh streaming** (`generate_content_stream` tương đương)
thay vì một phát. `CHAT_SYSTEM_PROMPT`, grounding, citation, fail‑closed **giữ ngữ nghĩa**; chỉ đổi *thời
điểm* áp fail‑closed (cuối luồng). Không stream nội dung thinking.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Perceived latency giảm mạnh ở giai đoạn **output**; giai đoạn **thinking** lấp bằng status.
- Trạng thái **chốt** của câu trả lời streaming **trùng hệt** bản blocking (grounding, citation, fail‑closed).
- Budget không rò khi client ngắt giữa luồng.

**Non-Goals:**
- Không bỏ blocking; không stream thinking verbatim; không đổi ngữ nghĩa grounding; không WebSocket/MQ;
  không reformulator/vector.

## Decisions

### D1 — Thêm `/chat/stream`, giữ `/chat` blocking; hai đường **chung** `ChatService`

Endpoint streaming là **biến thể trình bày** của cùng logic. Blocking giữ cho: client cũ, test đơn vị, và
④ (eval sinh câu trả lời — dễ đo trên bản một‑phát). Tránh nhân đôi logic: `ChatService` có đường async
generator, route blocking gọi bản gom‑hết, route stream gọi bản yield.

### D2 — Fail‑closed dưới streaming: **provisional → commit** (điểm cốt lõi)

Xung đột thật: fail‑closed hiện chạy trên câu **hoàn chỉnh** (`enforce_grounding` thay câu khẳng định‑không‑
marker bằng thông báo không đủ căn cứ), mà stream đã hiện chữ **trước** khi kiểm được.

Chọn: **stream text như tạm thời**; ở cuối luồng chạy `resolve_citations` + `enforce_grounding` trên câu đầy
đủ rồi phát sự kiện **`commit`** kèm citations. Hai nhánh:
- **Thường** (có marker hợp lệ): text đã stream đứng nguyên, citations gắn vào.
- **Hiếm** (fail‑closed): `commit` **thay** text tạm bằng thông báo không đủ căn cứ — widget hoán nội dung.

Bất biến giữ nguyên: **trạng thái chốt luôn grounded, trùng bản blocking**. Giá: một lần hoán hiếm gặp.

*Đã cân nhắc:*
- **Chỉ stream status, câu trả lời về nguyên khối cuối** — an toàn nhất nhưng **không** giảm độ trễ token,
  mất nửa lợi ích. Bỏ.
- **Stream không grounding** — vỡ bất biến fail‑closed. Bỏ.
- **Đệm tới khi chắc có marker rồi mới stream** — gần như mất streaming vì marker thường ở cuối câu. Bỏ.

### D3 — Khoảng **thinking** không có token → lấp bằng status, nói thật

Với Gemini thinking‑heavy, phần lớn 5–15s đầu là **suy nghĩ**, chưa có output token để stream. Nên "perceived
<0.5s" của báo cáo **không** đạt trọn nếu chỉ dựa vào token. ⑤ lấp khoảng đó bằng **sự kiện tiến trình**
(status), stream token thật khi output bắt đầu. Trung thực về giới hạn này trong docs (bám
`gemini-thinking-tokens`). **Không** stream nội dung thinking (nhiễu, dài).

### D4 — Sự kiện tiến trình bám giai đoạn pipeline thật, không giả

Status phát từ mốc thật: bắt đầu retrieval → "đang tìm trong hệ thống…"; ở câu mở rộng của ③ (sentinel →
lượt 2) → "bài này không đề cập, đang tìm toàn hệ thống…". Đây là **lý do ⑤ bổ trợ ③**: streaming làm độ trễ
2 lượt (10–45s) của mở rộng chịu được. Nếu ③ chưa land, chỉ có status của mode A/B thường.

### D5 — Logging budget **sống sót khi client ngắt**

Client có thể đóng stream giữa chừng (đổi trang, huỷ) sau khi model **đã** tốn tiền. Đường async generator
SHALL ghi `chat_logs` với `_calls_used` trong `finally` **kể cả** khi generator bị huỷ/ngắt — giữ đúng hợp
đồng "lượt đã tốn tiền phải được tính" của `chatbot-qa`. Đây là chỗ dễ rò nhất của streaming.

### D6 — Đổi scope giữa luồng đang stream → **huỷ stream**

Tương tác với ① (cô lập luồng): nếu người dùng đổi scope/insight khi đang stream, client SHALL huỷ request
(abort) → server dừng khi phát hiện ngắt (D5 vẫn log). Phần text dở **không** nhập vào luồng scope mới.

### D7 — Fast‑path/meta (②) không stream

Câu chào/meta trả preset tức thì — endpoint stream chỉ phát đúng một sự kiện `done` mang preset, không giả
lập gõ token. Giữ nhất quán: streaming chỉ cho câu thật sự chạy model.

## Risks / Trade-offs

- **[Hoán text khi fail‑closed]** → hiếm (model được dặn luôn cite hoặc nói "không tìm thấy"); **đo tần suất**
  hoán bằng log — cao bất thường là tín hiệu prompt/grounding lệch. Widget hoán mượt, không nhấp nháy.
- **[Proxy đệm SSE làm mất streaming]** (nginx buffer) → ghi lưu ý deploy; môi trường local/MVP của Hung ít
  gặp, nhưng docs phải nêu header chống buffer khi lên server thật.
- **[Client ngắt rò budget]** → D5 khoá bằng `finally` trong generator + test ngắt giữa luồng.
- **[Phức tạp ChatService tăng]** → giữ một nguồn logic, hai lối ra (gom/yield); không nhân đôi grounding.
- **[Đảo non‑goal streaming]** → có chủ đích (Hung duyệt); blocking vẫn còn nên không mất đường cũ.

## Migration Plan

1. `GeminiClient`: thêm hàm sinh streaming (yield chunk) song song `chat()` một‑phát.
2. `ChatService`: đường async generator phát `status`/`token`, cuối luồng chạy grounding → phát `commit`
   (citations hoặc fail‑closed); `finally` log budget kể cả khi ngắt (D5).
3. `routes/chat.py`: `POST /chat/stream` trả `StreamingResponse` SSE; `/chat` blocking giữ nguyên.
4. Frontend: đọc SSE bằng fetch stream (EventSource không POST được), render tăng dần + status +
   provisional→commit, huỷ khi đổi scope (D6).
5. Docs.

Rollback: xoá route stream + đường generator; widget quay lại `postChat` blocking. Không migration, không đổi
dữ liệu.

## Open Questions

- **Reformulator sau ⑤**: giờ đã có streaming che độ trễ, bật reformulator (một lượt tiền‑xử‑lý) đáng hay vẫn
  ưu tiên bản gộp‑từ‑khoá tất định? Quyết ở một change riêng, có ⑤ làm tiền đề.
- **Có nên stream cả ở mode B không hay chỉ A/expanded?** v1 stream mọi câu chạy model (cả B); cân nhắc nếu B
  thường ngắn thì lợi ích nhỏ.
- **Header/hạ tầng chống buffer** khi deploy thật (ngoài phạm vi local) — ghi lại, xử lý khi lên server.
