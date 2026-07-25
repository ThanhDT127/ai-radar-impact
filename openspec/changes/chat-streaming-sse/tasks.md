# Tasks: chat-streaming-sse

**Phase:** 2 (M8 Chatbot). Backend + Frontend + Test. Không migration, không n8n.

> Thứ tự: client streaming → service async generator (grounding cuối luồng + budget khi ngắt) → route SSE →
> widget render tăng dần → xác minh mắt. Giữ endpoint blocking nguyên vẹn suốt.

## 1. Sinh streaming ở GeminiClient (Backend/AI)

- [ ] 1.1 Thêm hàm sinh **streaming** (yield từng chunk text) song song `chat()` một‑phát; cùng tham số system+prompt, cùng cấu hình (không structured output). **DoD:** gọi thử in ra token dần; `chat()` cũ không đổi.
- [ ] 1.2 Trả về cả **số lượt gọi** để service cộng `_calls_used` (streaming vẫn 1 lượt/câu, 2 nếu mở rộng ③). **DoD:** đếm lượt khớp bản blocking.

## 2. Đường async generator trong ChatService (Backend)

- [ ] 2.1 `ChatService` có đường generator phát sự kiện: `status` (mốc pipeline), `token` (chunk câu trả lời), `commit` (citations hoặc fail‑closed), `error`. Giữ **một** nguồn logic; route blocking gọi bản gom‑hết. **DoD:** không nhân đôi logic grounding giữa hai lối ra.
- [ ] 2.2 **Provisional → commit** (design D2): stream token thô; cuối luồng chạy `resolve_citations` + `enforce_grounding` trên câu đầy đủ; phát `commit` mang citations, hoặc — nếu fail‑closed — mang **text thay thế** để widget hoán. **DoD:** ca có marker → text giữ + citations; ca khẳng định‑không‑marker → commit ra text không‑đủ‑căn‑cứ; **trạng thái chốt trùng bản blocking** trên cùng input.
- [ ] 2.3 **Budget sống sót khi ngắt** (design D5): ghi `chat_logs` với `_calls_used` trong `finally` của generator kể cả khi bị huỷ/ngắt giữa luồng. **DoD:** test giả lập ngắt sau khi model đã trả về → `chat_logs` vẫn ghi, budget không rò.
- [ ] 2.4 Status của câu **mở rộng** (③): khi sentinel bắn → phát status "đang tìm toàn hệ thống…" trước lượt 2 (design D4). **DoD:** với ③ đã land, câu out‑of‑scope phát đúng chuỗi status; không có ③ thì chỉ status A/B thường.
- [ ] 2.5 Fast‑path/meta (②): endpoint stream phát đúng một `done`/`commit` mang preset, **không** stream token giả (design D7). **DoD:** "xin chào" qua stream ra ngay, 0 lượt gọi.

## 3. Route SSE (Backend)

- [ ] 3.1 `POST /api/v1/chat/stream` trả `StreamingResponse` `text/event-stream`, ánh xạ sự kiện generator → SSE. Kiểm quota **đầu luồng** như blocking. **DoD:** curl thấy các dòng `event:`/`data:` chảy dần.
- [ ] 3.2 `POST /api/v1/chat` blocking **giữ nguyên** hành vi/response. **DoD:** test cũ của `/chat` vẫn pass không sửa.
- [ ] 3.3 Ngắt kết nối phía client → server dừng sinh và đi vào `finally` (nối task 2.3). **DoD:** đóng client giữa luồng, log server cho thấy dừng + ghi budget.

## 4. Widget streaming (Frontend)

- [ ] 4.1 `api/chat.ts`: hàm đọc SSE bằng **fetch + ReadableStream** (EventSource không POST được), parse `status`/`token`/`commit`/`error`. **DoD:** nhận và ráp token thành câu.
- [ ] 4.2 `ChatWidget`: render **tăng dần** vào bong bóng bot, hiện **status** thay spinner đơn; ở `commit` gắn citations, hoặc hoán text nếu fail‑closed. **DoD:** thấy chữ chảy + dòng trạng thái; đổi spinner "Đang tìm…" thành status thật.
- [ ] 4.3 **Huỷ khi đổi scope** (design D6, nối ①): đổi insight/scope khi đang stream → abort request; phần dở không nhập luồng scope mới. **DoD:** stream ở A, chuyển B giữa chừng → stream A bị huỷ, luồng B sạch.
- [ ] 4.4 Nhãn câu trả lời mở rộng (`mode="expanded"`) vẫn hiển thị đúng khi đến qua stream (nối ③). **DoD:** câu mở rộng streaming vẫn được đánh dấu toàn‑hệ‑thống.
- [ ] 4.5 Giữ nút Gửi disabled khi đang stream (chống thundering herd của Nguy hiểm #1). **DoD:** không gửi được câu mới khi luồng chưa xong.

## 5. Xác minh bằng mắt (Test)

- [ ] 5.1 Hỏi mode A một câu dài: xác nhận thấy status trong lúc thinking rồi token chảy; citations gắn ở cuối; bấm citation mở đúng tin. **DoD:** ghi lại (ảnh/ghi chú) chuỗi status→token→citations.
- [ ] 5.2 Ca fail‑closed: dựng câu khiến model khẳng định không marker → xác nhận `commit` hoán sang không‑đủ‑căn‑cứ, không để lại text ungrounded. **DoD:** trạng thái cuối khớp bản blocking cho cùng câu.
- [ ] 5.3 Ca ngắt: đóng widget/đổi trang giữa luồng → không lỗi, budget vẫn ghi. **DoD:** khớp task 2.3/3.3.

## 6. Tài liệu (làm sau khi code đã chạy)

- [ ] 6.1 `CLAUDE.md` mục chat: hai endpoint (`/chat` blocking + `/chat/stream` SSE); **khoảng thinking không có token** nên status lấp; **provisional→commit** giữ fail‑closed; budget log sống sót khi ngắt. **DoD:** người đọc hiểu vì sao vẫn có độ trễ đầu dù đã streaming.
- [ ] 6.2 Ghi lưu ý deploy: header chống buffer SSE (nginx) khi lên server thật (design Open Questions). **DoD:** có dòng cảnh báo cho lúc rời local.
