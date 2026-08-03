## Why

Streaming đã land (`chat-streaming-sse`, 27/07) với kết luận đo được: **TTFT thật không cắt
được, status mới là thứ chữa** — 85% TTFT nằm ở lượt gọi model, và ba hướng tối ưu prompt đều
đã đo và loại ở `chat-context-depth`.

Nhưng phần status hiện chỉ khai thác được một phần nhỏ của chính kết luận đó:

- Đúng **4 chuỗi cứng** (`chat_service.py:87-90`), trong đó chỉ `_reading_status` mang số liệu
  thật của lượt. Câu toàn cục điển hình thấy đúng **2 mốc**.
- Frontend **THAY** một dòng (`ChatWidget.tsx:188` — `{...p, status: text}`), nên mốc trước
  biến mất khi mốc sau tới: người dùng không thấy tiến trình, chỉ thấy một dòng nhấp nháy.
- Pipeline **im lặng ở nhiều mốc thật đã tồn tại**: lọc/xếp hạng xong, tin ghim từ history,
  tín hiệu đoạn thân bài, và — đáng kể nhất — **lượt hỏi lại khi câu trả lời bị cắt**
  (`chat-answer-completeness`), nơi người dùng chờ thêm nguyên một lượt gọi model mà màn hình
  không nói gì.

Đây là hạ tầng UX mà `chat-web-fallback` sẽ dựa vào: ở đó TTFT dài hơn hẳn (3 bước model +
fetch), nên nếu status không khá lên trước thì tính năng đó land vào một giao diện đứng hình.

## What Changes

- Phát status ở các **mốc thật đang im lặng**: xếp hạng xong (kèm số tin khớp), ghim tin từ
  history (kèm tiêu đề), hỏi lại vì câu trả lời bị cắt.
- Widget **xếp chồng** status thay vì thay thế: mốc đã qua giữ lại ở dạng mờ + dấu hoàn thành,
  mốc hiện tại đậm. Chốt câu trả lời thì cả khối biến mất như hiện nay.
- Sự kiện `status` mang thêm trường `key` ổn định để widget phân biệt mốc mới với mốc cập
  nhật, thay vì so sánh chuỗi hiển thị.

## Capabilities

### New Capabilities
<!-- Không có: đây là khai thác sâu hơn một cơ chế đã tồn tại. -->

### Modified Capabilities
- `chat-qa-service`: thêm yêu cầu *status phát từ mốc thật và mang số liệu của lượt đó*, mở
  rộng danh sách mốc bắt buộc.
- `chat-web-widget`: status hiển thị dạng **danh sách tích luỹ**, không phải một dòng bị ghi đè.

## Non-goals

- **KHÔNG** xoay vòng cách nói đồng nghĩa để "đỡ lặp". Luật đã chốt tại `chat_service.py:83-86`
  và `108-109`: status phát từ **mốc thật**, *"nói sai việc còn tệ hơn nói chung chung"*. Đa
  dạng phải đến từ dữ liệu thật của lượt, không từ từ điển đồng nghĩa. Đây là **bác bỏ có chủ
  đích**, không phải hoãn.
- **KHÔNG** thêm status chạy theo đồng hồ / thanh tiến trình giả. Cùng lý do.
- **KHÔNG** đụng `_rank`, `build_context`, grounding, hay bất kỳ thứ gì quyết định *nội dung*
  câu trả lời ⇒ không phải chốt lại baseline RS, không cần `chat_answer_harness --live`.
- **KHÔNG** làm mượt token phía client (gộp chunk thô của Vertex). Vấn đề render, độc lập với
  mốc tiến trình — tách ra change khác.
- **KHÔNG** phát status cho lượt gọi bộ phân loại ý định tầng 2 (3,6% câu): mốc đó nằm
  **trước** khi biết câu hỏi có phải câu tra cứu không, nói ra chỉ gây nhiễu cho câu chào.

## Phase

**Phase 2** — M8 (Chat Q&A) + M6 (Dashboard). Không đụng M1–M7 pipeline, không đụng DB.

## Dependency

Không phụ thuộc change nào đang mở. **`chat-web-fallback` phụ thuộc change này** — nên land
cái này trước.
