## Context

**Module: M6 (Dashboard) + M8 (Chat Q&A), chỉ phần frontend.**

- **API bị ảnh hưởng:** không có. `POST /api/v1/chat` và `POST /api/v1/chat/stream` giữ nguyên
  payload, nguyên hợp đồng sự kiện. Change này không gửi thêm một byte nào lên server.
- **Bảng DB bị ảnh hưởng:** không có. Không migration.
- **AI/LLM:** không có lượt gọi model mới, không đụng prompt, không đụng grounding, không đụng
  `_rank`. ⇒ Không chốt lại baseline RS, không chạy `chat_answer_harness --live`.
- **n8n / delivery:** không liên quan.

Hiện trạng đo được (đọc mã, 03/08/2026):

| | |
|---|---|
| Nơi giữ hội thoại | `useState` trong `ChatWidget.tsx` (`messages`, `workingSet`, `open`, `pending`) |
| Nơi lưu bền | **không có** — client lẫn server |
| `history` gửi lên | do client dựng lại từ `messages` mỗi lượt (`ChatWidget.tsx:207`) |
| Sau F5 ở trang danh sách | mất 100% |
| Sau F5 ở `/insights/:id` | mất hội thoại, **giữ 1 chip** working set (effect dòng 132) |
| Storage đang dùng trong frontend | `localStorage` cho `theme` và `radar-view-mode` — chưa có tiện ích chung |

Ràng buộc kế thừa, không được phá:

- **Chỉ câu đã `commit` mới nhập luồng** (`chat-streaming-sse` D2): `pending.text` là text TẠM,
  ở ca fail-closed nó là một câu **hoàn toàn khác** câu cuối.
- **`citations[].insight_id` phải sống trong `history`** (`chat-history-pinning`): thiếu nó thì
  server không ghim gì và **52%** cặp (tin đã bàn, chủ đề mới) rơi khỏi top-60 — im lặng.
- **`n` là số marker do server cấp**, không phải chỉ số mảng (`chat-citation-integrity`).

## Goals / Non-Goals

**Goals**

- F5 / back-forward / khôi phục crash trong **cùng một tab** không làm mất câu chữ đã trao đổi.
- Luồng hội thoại **độc lập** với mọi thao tác ngữ cảnh (bỏ chip, bỏ hết chip, đổi bài, điều
  hướng).
- Suy giảm êm khi storage không dùng được: mất trí nhớ còn hơn vỡ widget.
- Không thêm một lượt gọi mạng, một truy vấn DB, hay một byte prompt nào.

**Non-Goals:** đa tab dùng chung; sống qua đóng tab; lưu phía server; nối lại luồng đang chảy.

## Bất biến change này thiết lập

```
A — Luồng hội thoại thuộc về TAB, không thuộc về ngữ cảnh.
    Không thao tác ngữ cảnh nào (bỏ chip, bỏ hết chip, đổi bài, điều hướng, F5)
    được phép làm mất câu chữ đã trao đổi.

B — Mỗi tab một luồng riêng. Không tab nào đọc/ghi luồng của tab khác.

C — Chỉ nội dung ĐÃ CHỐT mới được lưu. Text đang stream không bao giờ chạm storage.
```

## Decisions

### D1 — `sessionStorage`, không phải `localStorage`

Yêu cầu là per-tab (bất biến B). `sessionStorage` cho đúng ngữ nghĩa đó **miễn phí**:

| Thao tác | `sessionStorage` | `localStorage` |
|---|---|---|
| F5 / Ctrl+R | giữ | giữ |
| Back qua trang ngoài rồi Forward | giữ | giữ |
| Khôi phục sau crash tab | giữ | giữ |
| Tab thứ 2 | **luồng riêng** ✅ | **dùng chung** ⚠️ last-writer-wins |
| Đóng tab | mất (chấp nhận) | giữ |

Chọn `localStorage` sẽ phải tự dựng lại tính per-tab bằng một `tabId` phụ — tức là dùng
`sessionStorage` gián tiếp, đắt hơn mà không mua thêm gì trong phạm vi đã chốt.

### D2 — MỘT khoá phẳng cho cả tab. Khoá KHÔNG được mang ngữ cảnh

Đây là quyết định trung tâm, và nó tồn tại vì một lỗi đã xảy ra thật.

```
❌ SAI — tái sinh chế độ hỏng của `chat-context-isolation`:
   sessionStorage[`radar-chat:${scopeKey}`]        ← khoá mang scope
   sessionStorage[`radar-chat:${workingSetIds}`]   ← bỏ chip = đổi khoá = "mất" hội thoại

✅ ĐÚNG:
   sessionStorage['radar-chat-v1'] = {
     v: 1,
     messages:   Message[],   ← nguồn sự thật của cuộc hội thoại
     workingSet: Ref[],       ← ngữ cảnh KÈM THEO, trường ngang hàng
     open:       boolean,
   }
```

`workingSet` nằm **trong** cùng object nhưng là một trường ngang hàng `messages`, không phải
một phần của khoá. Xoá hết chip ⇒ `workingSet: []`, `messages` không suy suyển. Đây là chỗ duy
nhất mà "làm cho tiện" sẽ hồi sinh lỗi cũ, nên nó được khoá bằng một test đặt tên tường minh
chứ không nằm lẫn trong test khôi phục chung.

### D3 — Lưu trọn `Message`, đặc biệt là `citations[].insight_id`

Cám dỗ tự nhiên là chỉ lưu `{role, content}` cho gọn. Làm thế thì sau F5 mọi lượt cũ mất
`insight_id` ⇒ cơ chế ghim của `chat-history-pinning` **tắt trong im lặng**, giao diện trông y
hệt, và người dùng chỉ thấy bot "quên" chuyện vừa bàn. Lưu trọn `citations` (`n`, `kind`,
`insight_id`, `title`, `source_url`).

### D4 — KHÔNG lưu `pending`

Bất biến C. Ghi diễn ra ở `useEffect` phụ thuộc `[messages, workingSet, open]` — `pending`
không nằm trong danh sách, nên vừa đúng bất biến vừa tránh ghi storage mỗi token.

### D5 — Phiên bản hoá: lệch thì VỨT, không migrate

Hình dạng `Citation` đổi liên tục trong repo này: `n` thêm ở `chat-citation-integrity` (27/07),
`kind` thêm ở `chat-web-fallback` (03/08). Một blob cũ hồi sinh vào code mới sẽ giải marker sai
mà không có gì đỏ. Khoá mang `v`; đọc thấy `v` khác hằng số hiện tại ⇒ bỏ qua và bắt đầu luồng
trống. Migrate dữ liệu chat cũ không đáng giá bằng rủi ro trỏ sai citation.

### D6 — KHÔNG lưu `searchSuggestions`

Hai lý do độc lập:

1. Nó là HTML đi thẳng vào `dangerouslySetInnerHTML`. Hồi sinh HTML từ storage mở rộng ranh
   giới tin cậy từ *"response server trả trong phiên này"* sang *"bất cứ thứ gì nằm trong
   storage"*.
2. Nó là UI tuân thủ gắn với **một truy vấn tại một thời điểm**; hiển thị lại một khối gợi ý
   tìm kiếm đã cũ không phục vụ mục đích tuân thủ nào.

Bong bóng khôi phục mất phần gợi ý; câu chữ và citation vẫn nguyên.

### D7 — Lượt hỏi treo: GIỮ + đánh dấu gián đoạn + Thử lại

`send()` đẩy bong bóng user vào `messages` **trước** khi stream chạy
(`ChatWidget.tsx:225`), nên nó được lưu, còn câu trả lời thì chưa:

```
khôi phục:
  [user] "so sánh hai bài này"     ← còn đây
  [  ?  ]                          ← trống; server ĐÃ tính tiền lượt đó (D5 của streaming)
```

Phát hiện bằng **cấu trúc**, không bằng cờ: message cuối cùng có `role === 'user'` ⇒ lượt đó
chưa được trả lời. Không thêm trường trạng thái vào `Message` — một cờ được ghi ở một chỗ và
đọc ở chỗ khác là một cơ hội để hai nguồn sự thật lệch nhau.

Widget hiện một bong bóng thông báo gián đoạn kèm **Thử lại**. Việc này biến `retryLast()` từ
đường hiếm thành đường thường ⇒ **phải sửa bug nhân đôi câu hỏi** của nó trong cùng change:
hiện nó lọc bong bóng lỗi rồi gọi `send()`, mà `send()` lại append một bong bóng user nữa.

### D8 — Nút "Cuộc trò chuyện mới": nhỏ, ở header panel

F5 đang là nút reset duy nhất. Sau change này một luồng dài/lạc đề sẽ không còn đường thoát, mà
`history` vẫn được gửi lên mỗi lượt (tốn token, và cơ chế ghim bám vào chủ đề cũ).

Vị trí: header panel, cạnh nút đóng, dạng icon-button nhỏ cùng cỡ `styles.iconBtn` sẵn có —
không phải nút to trong khu vực nhập liệu. Lý do: đây là thao tác **hiếm và huỷ dữ liệu**; đặt
cạnh chỗ gõ câu hỏi là mời bấm nhầm. Nó xoá `messages`, `workingSet`, và khoá storage.

Không thêm hộp thoại xác nhận ở v1: thao tác này ở xa luồng thao tác chính, và một dialog cho
một widget chat là nặng tay. Nếu đo được người dùng bấm nhầm thì mở lại quyết định này.

### D9 — Thứ tự khôi phục vs effect route

`useState` initializer chạy **trước** mọi `useEffect`, nên working set từ storage có mặt trước
khi effect route (`ChatWidget.tsx:132`) chạy. Nếu bài đang mở đã nằm trong tập khôi phục,
`addRef` giữ nguyên (nó kiểm tra `some(r => r.id === ref.id)`); nếu chưa, nó được thêm vào và
`slice(-MAX_REFS)` đẩy mục cũ nhất ra — **đúng hành vi của một lần điều hướng bình thường**,
không phải một đường riêng cần xử lý.

### D10 — Storage hỏng thì im lặng suy giảm

`sessionStorage` ném lỗi khi hết quota hoặc bị chặn (Safari private, một số cấu hình doanh
nghiệp). Mọi lần đọc/ghi bọc `try/catch`; thất bại ⇒ widget chạy đúng như hôm nay. Chat mất trí
nhớ còn hơn chat không mở được.

Trần dung lượng: giữ **50 message** gần nhất khi ghi (`sessionStorage` ~5MB/origin, một câu trả
lời ~1–4KB ⇒ dư rộng). Phần dôi ra chỉ để đọc lại — `MAX_HISTORY_TURNS` vốn chỉ gửi 10 tin nhắn
lên server, nên cắt ở 50 không đụng tới thứ server nhìn thấy.

### D11 — Khôi phục `open` KHÔNG phải "tự động mở"

Spec hiện tại nói *"Widget SHALL không tự động mở"*. Câu đó nhắm vào việc widget tự ý bật lên
khi người dùng chưa đụng tới nó. Khôi phục đúng trạng thái người dùng để lại là chuyện khác —
nhưng nó **đủ gần để phải nói rõ**, nếu không thì lần sửa spec sau sẽ đọc thành mâu thuẫn. Yêu
cầu được sửa lời tường minh thay vì để hai câu đá nhau ngầm.

## Risks / Trade-offs

| Rủi ro | Đánh giá |
|---|---|
| Đóng tab vẫn mất hội thoại | Chấp nhận theo yêu cầu. Đường nâng cấp: đổi D1 sang `localStorage` + `tabId`, không phải viết lại. |
| Blob cũ sau khi đổi shape `Message` | D5 vứt sạch. Giá: người dùng đang mở tab lúc deploy mất luồng đúng một lần. |
| Máy dùng chung: hội thoại còn đó cho người ngồi sau | Giới hạn ở đúng tab đó và mất khi đóng tab — hẹp hơn `localStorage` một bậc. |
| Bấm "Cuộc trò chuyện mới" nhầm | D8 đặt xa vùng gõ; không có undo ở v1. |

## Migration Plan

Không có migration dữ liệu. Deploy frontend là xong. Rollback = gỡ lớp persistence, hành vi về
đúng như hôm nay; blob còn sót trong `sessionStorage` của người dùng sẽ tự hết khi đóng tab.

## Open Questions

Không còn. Hai điểm từng mở (xử lý lượt hỏi treo; có nút reset hay không) đã chốt ở D7 và D8.
