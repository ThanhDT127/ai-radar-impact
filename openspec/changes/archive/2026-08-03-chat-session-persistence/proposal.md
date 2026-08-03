## Why

Toàn bộ cuộc hội thoại chat sống trong `useState` của `ChatWidget.tsx` và **không có chỗ nào
khác giữ nó** — client không lưu, còn server thì cố ý không lưu (`chat_logs`: *"KHÔNG lưu nội
dung câu hỏi/câu trả lời"*). Vì `history` do client gửi lên mỗi lượt, client mất trí nhớ =
cuộc hội thoại chết, kể cả khi server vẫn khoẻ.

Hệ quả: **F5 hoặc back về một trang ngoài SPA là xoá sạch**. Người dùng vừa dựng xong một
working set ba bài và hỏi năm lượt, lỡ tay Ctrl+R là mất hết — kể cả những lượt đã trả tiền
cho model. Tệ hơn, việc mất mát hiện **không đều**: nếu đang ở `/insights/:id` thì effect ở
`ChatWidget.tsx:132` dựng lại đúng một chip working set, nên sau F5 người dùng thấy *"Đang đọc
kỹ: <tên bài>"* còn hội thoại trắng trơn — khôi phục một nửa, và mất đúng nửa quan trọng.

Đây cũng là lần thứ hai cùng một triệu chứng: `chat-context-isolation` (commit `8d5ffdb`) từng
đánh khoá `threads` **theo scope**, nên rời bài là luồng của bài đó biến khỏi màn hình.
`chat-context-depth` đã gộp về một luồng, nhưng luồng đó chỉ sống trong RAM.

## What Changes

- Luồng hội thoại (câu chữ + citation + working set + trạng thái mở panel) được **lưu bền theo
  tab** và khôi phục khi tài liệu tải lại: F5, back/forward qua trang ngoài, khôi phục sau
  crash tab.
- Chỗ lưu dùng **một khoá phẳng cho cả tab**. Không đánh khoá theo scope / bài đang xem /
  working set — đó chính là lỗi cũ, và nó khiến "bỏ hết chip" đồng nghĩa với "mất hội thoại".
- F5 giữa lúc đang trả lời để lại một lượt hỏi treo: widget **giữ câu hỏi đó**, đánh dấu là bị
  gián đoạn và cho **Thử lại** — không lặng lẽ vứt.
- Thêm nút nhỏ **"Cuộc trò chuyện mới"** ở header panel. F5 đang là nút xoá hội thoại duy nhất;
  bỏ nó đi mà không thay bằng gì thì một luồng dài/lạc đề không còn đường thoát, trong khi
  `history` vẫn được gửi lên mỗi lượt.
- Sửa kèm `retryLast()`: nó lọc bong bóng lỗi rồi gọi `send()`, mà `send()` lại append thêm một
  bong bóng user nữa ⇒ **nhân đôi câu hỏi**. Bug đang ẩn vì đường lỗi hiếm; change này biến nó
  thành đường đi thường xuyên.

## Capabilities

### New Capabilities
<!-- Không có capability mới: đây là độ bền của một bề mặt đã tồn tại. -->

### Modified Capabilities
- `chat-web-widget`: thêm yêu cầu *hội thoại bền vững theo tab*; sửa yêu cầu "không tự động mở"
  để phân biệt **khôi phục trạng thái người dùng** với **tự ý mở**; ghi rõ luồng hội thoại
  **độc lập** với working set.

## Non-goals

- **KHÔNG** chia sẻ hội thoại giữa các tab. Mỗi tab một luồng riêng — đúng mô hình hiện tại, và
  dùng chung một khoá cho nhiều tab là để hai luồng trộn vào nhau trong im lặng.
- **KHÔNG** giữ hội thoại sau khi **đóng tab**. Chấp nhận có chủ đích: đó là ranh giới của
  `sessionStorage`, và nó cũng là giới hạn tự nhiên của một bản ghi không có chủ sở hữu.
- **KHÔNG** lưu hội thoại phía server, **KHÔNG** thêm `conversation_id`. Hệ thống chưa có auth
  nên "định danh" cũng chỉ là một token do client giữ — tức vẫn dựa vào storage của trình
  duyệt, mà lại phải đảo ngược quyết định "chat_logs chỉ metadata", thêm bảng, thêm retention.
  Bác bỏ có bằng chứng về chi phí, không phải hoãn.
- **KHÔNG** nối lại luồng SSE đang chảy sau khi tải lại. Cần task pipeline sống ngoài request và
  có địa chỉ để gắn lại — một change riêng, lớn hơn hẳn.
- **KHÔNG** đụng backend: không endpoint mới, không migration, không lượt gọi model ⇒ không
  chạy lại RS harness, không `chat_answer_harness --live`.

## Phase

**Phase 2** — M6 (Dashboard) + M8 (Chat Q&A), phần frontend. Không đụng M1–M7 pipeline, không
đụng DB.

## Dependency

Không phụ thuộc change nào đang mở. Đứng trên `chat-context-depth` (một luồng) và
`chat-history-pinning` (`citations[].insight_id` trong `history`).
