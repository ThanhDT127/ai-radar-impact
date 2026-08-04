# Proposal: chat-streaming-sse

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — phủ phần 2 khung To‑Be: Kiến trúc Realtime).

## Why

`POST /api/v1/chat` là JSON blocking. Độ trễ **thật đo được 5–22,6s** (thinking tokens 121→3.791 token/câu),
còn widget chỉ hiện một spinner "Đang tìm trong hệ thống…". Báo cáo To‑Be Nguy hiểm #1: người dùng nhìn màn
hình đứng ~10s tưởng treo → bấm Gửi lại nhiều lần → **thundering herd**, đốt quota và quá tải backend.

`chat-scope-routing` (③) làm chuyện này nặng thêm: câu mở rộng tốn **2 lượt gọi** → **10–45s**. Chính vì độ
trễ này mà **reformulator đã bị hoãn cho tới khi có streaming** (chốt ở ②). ⑤ là mảnh mở khoá đó.

Đây là đảo một non‑goal ("không streaming") mà các change chat trước cố ý chốt cho MVP — **Hung đã duyệt đảo**
để phủ đủ khung 7 phần.

## What Changes

- **Endpoint streaming mới `POST /api/v1/chat/stream`** (SSE) — trả **token câu trả lời** ngay khi model
  sinh, cùng **sự kiện tiến trình** (status). Giữ nguyên `POST /api/v1/chat` blocking cho client cũ, test,
  và eval harness (④).
- **Sự kiện tiến trình thật, không trang trí** — bám đúng giai đoạn pipeline: đang tìm trong hệ thống; ở câu
  mở rộng của ③: "bài này không đề cập, đang tìm toàn hệ thống…". Lấp **khoảng thinking** (chưa có token để
  stream) bằng status thay vì để trống.
- **Fail‑closed giữ nguyên bất biến qua "provisional → commit"**: stream text dạng tạm; chạy
  `resolve_citations` + `enforce_grounding` trên câu **hoàn chỉnh** ở cuối luồng rồi gửi sự kiện chốt kèm
  citations. Ca hiếm fail‑closed: sự kiện chốt **thay** text tạm bằng thông báo không đủ căn cứ. Trạng thái
  cuối cùng luôn grounded y hệt bản blocking.
- **Widget render tăng dần** thay spinner: token chảy vào bong bóng, status hiện tiến trình, citations gắn ở
  cuối.

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-qa-service`: hệ thống SHALL cung cấp endpoint streaming phát token + sự kiện tiến trình, với grounding
  và fail‑closed áp ở cuối luồng sao cho trạng thái chốt giống hệt endpoint blocking.
- `chat-web-widget`: widget SHALL render câu trả lời theo luồng và hiển thị trạng thái tiến trình thay cho
  spinner đơn.

## Non-goals

- **Không** bỏ endpoint blocking — giữ cho client cũ, test, và ④.
- **Không** stream nguyên văn nội dung thinking — chỉ status generic khi đang suy nghĩ (tránh nhiễu).
- **Không** đổi ngữ nghĩa grounding/citation/fail‑closed — trạng thái **chốt** phải trùng bản blocking.
- **Không** thêm reformulator/vector — reformulator quyết lại **sau** ⑤; vector là ⑥.
- **Không** hạ tầng WebSocket/message queue — SSE một chiều đủ; giữ đơn giản (1 dev).

## Dependencies

- `chatbot-qa` (archive 22/07/2026) — `ChatService` và endpoint được mở rộng thuộc change đó.
- **`chat-scope-routing` (③) — mềm**: streaming làm status "đang mở rộng" và độ trễ 2 lượt của ③ chịu được;
  ⑤ chạy không cần ③ nhưng bổ trợ nhau. Sự kiện tiến trình của câu mở rộng chỉ có nghĩa khi ③ đã land.
- **`chat-context-isolation` (①) — mềm**: đổi scope giữa luồng đang stream phải huỷ stream (design D6).

## Impact

- **Backend**: `ai/gemini_client.py` (hàm sinh **streaming**), `services/chat_service.py` (đường async
  generator + logging budget sống sót khi client ngắt), `routes/chat.py` (`StreamingResponse` SSE), test.
- **Frontend**: `api/chat.ts` (đọc SSE bằng fetch stream), `components/ChatWidget.tsx` (render tăng dần,
  status, provisional→commit, huỷ khi đổi scope), test.
- **Docs**: `CLAUDE.md` — hai endpoint, khoảng thinking không có token, provisional→commit của fail‑closed.
- **Không** migration, không đổi budget/quota (vẫn cùng số lượt gọi model).
