> Thứ tự bắt buộc: tiện ích lưu trữ (hình dạng + phiên bản) → nối vào widget → hai tính năng
> kéo theo (lượt treo, nút hội thoại mới) → test.
> Lý do: hình dạng dữ liệu lưu là hợp đồng mà mọi phần sau bám vào; định nghĩa sau thì phải
> sửa ngược ba chỗ.
>
> **Change này KHÔNG đụng backend** — không endpoint, không migration, không lượt gọi model.
> ⇒ Không chạy lại RS harness, không `chat_answer_harness --live`. Task nào buộc phải sửa
> `_rank` / `build_context` / grounding / schema chat là **sai phạm vi** — dừng và xem lại design.

## 1. Frontend — tầng lưu trữ

- [x] 1.1 Tạo `frontend/src/components/chatSession.ts`: định nghĩa kiểu `PersistedSession` (`v`, `messages`, `workingSet`, `open`), hằng số `STORAGE_KEY = 'radar-chat-v1'` và `SESSION_VERSION`. **DoD:** một chỗ duy nhất định nghĩa hình dạng; `grep` ra đúng một hằng số khoá. (P2)
- [x] 1.2 Viết `loadSession()` / `saveSession()` / `clearSession()` trên `sessionStorage`, bọc `try/catch` cả đọc lẫn ghi. **DoD:** storage ném lỗi ⇒ `loadSession()` trả `null`, `saveSession()` no-op, không log ồn, không throw ra ngoài (design D10). (P2, phụ thuộc 1.1)
- [x] 1.3 `loadSession()` bỏ qua dữ liệu lệch `v` hoặc JSON hỏng, trả `null`. **DoD:** không có nhánh migrate nào; blob phiên bản cũ không bao giờ chảy vào state (design D5). (P2, phụ thuộc 1.2)
- [x] 1.4 `saveSession()` cắt còn **50** message gần nhất và **lược trường `searchSuggestions`** khỏi mỗi message trước khi ghi. **DoD:** blob ghi ra không chứa khoá `searchSuggestions`; `citations` (gồm `n`, `kind`, `insight_id`, `title`, `source_url`) giữ **nguyên vẹn** (design D3, D6). (P2, phụ thuộc 1.2)

## 2. Frontend — nối vào widget

- [x] 2.1 Khởi tạo `messages` / `workingSet` / `open` trong `ChatWidget.tsx` bằng `useState(() => loadSession() ?? …)`. **DoD:** khôi phục xảy ra trước mọi `useEffect`, nên effect route ở dòng 132 chạy sau và hành xử như một lần điều hướng bình thường (design D9). (P2, phụ thuộc 1.2)
- [x] 2.2 Thêm `useEffect` ghi storage với deps đúng `[messages, workingSet, open]`. **DoD:** `pending` KHÔNG có trong deps ⇒ không ghi một lần nào trong lúc token đang chảy (design D4, bất biến C). (P2, phụ thuộc 2.1)
- [x] 2.3 Kiểm chứng khoá lưu không mang ngữ cảnh: không có chuỗi khoá nào được dựng từ `scopeKey` / `routeInsightId` / `workingSet`. **DoD:** `grep` toàn bộ `ChatWidget.tsx` + `chatSession.ts` không thấy template string nào nối khoá (design D2, bất biến A). (P2, phụ thuộc 1.1)

## 3. Frontend — lượt hỏi bị gián đoạn

- [x] 3.1 Suy ra trạng thái gián đoạn từ **cấu trúc**: `messages.at(-1)?.role === 'user'` và không có `pending`. **DoD:** không thêm trường trạng thái nào vào `Message`; không ghi cờ nào xuống storage (design D7). (P2, phụ thuộc 2.1)
- [x] 3.2 Render bong bóng thông báo gián đoạn kèm nút **Thử lại** cho ca 3.1, dùng lại kiểu bong bóng lỗi sẵn có. **DoD:** chỉ hiện khi lượt cuối là của người dùng và không có luồng nào đang chạy. (P2, phụ thuộc 3.1)
- [x] 3.3 Sửa `retryLast()` **không nhân đôi bong bóng câu hỏi**: gửi lại mà không append thêm lượt user, hoặc gỡ lượt user cũ trước khi gửi — chọn một và ghi rõ lý do trong comment. **DoD:** sau khi thử lại, màn hình có đúng **một** bong bóng cho câu hỏi đó; `history` gửi lên không chứa lượt trùng. (P2, phụ thuộc 3.2)

## 4. Frontend — nút "Cuộc trò chuyện mới"

- [x] 4.1 Thêm icon-button nhỏ ở header panel, cạnh nút đóng, dùng `styles.iconBtn` sẵn có, kèm `aria-label` tiếng Việt. **DoD:** không nằm trong khu vực nhập câu hỏi; cỡ ngang bằng nút đóng (design D8). (P2)
- [x] 4.2 Hành vi: xoá `messages`, xoá `workingSet`, gọi `clearSession()`, **giữ panel mở**. **DoD:** sau khi bấm, panel hiện đúng trạng thái trống như lần mở đầu; tải lại trang không thấy lượt cũ quay lại. (P2, phụ thuộc 4.1, 1.2)

## 5. Test

- [x] 5.1 `chatSession.test.ts`: round-trip giữ **nguyên vẹn** `citations[].insight_id`. **DoD:** đỏ nếu ai đó rút gọn blob còn `{role, content}` — đây là lưới cho cơ chế ghim (design D3). (P2, phụ thuộc 1.4)
- [x] 5.2 `chatSession.test.ts`: `v` lệch ⇒ `loadSession()` trả `null`; JSON hỏng ⇒ `null`. **DoD:** 2 test, không nhánh migrate nào được gọi. (P2, phụ thuộc 1.3)
- [x] 5.3 `chatSession.test.ts`: `sessionStorage` ném lỗi ở cả `getItem` lẫn `setItem` ⇒ không throw ra ngoài. **DoD:** widget-level smoke vẫn render được. (P2, phụ thuộc 1.2)
- [x] 5.4 `chatSession.test.ts`: blob ghi ra không chứa `searchSuggestions`, và bị cắt còn 50 message. **DoD:** 2 assertion. (P2, phụ thuộc 1.4)
- [x] 5.5 `ChatWidget.persistence.test.tsx` — **test mang tên bất biến**: `xoa_het_working_set_khong_dung_toi_hoi_thoai`. Bỏ lần lượt hết chip rồi khẳng định các bong bóng vẫn còn và `history` của câu hỏi kế tiếp vẫn đủ lượt. **DoD:** đỏ nếu ai đó đánh khoá storage theo working set (bất biến A). (P2, phụ thuộc 2.2)
- [x] 5.6 `ChatWidget.persistence.test.tsx`: unmount → mount lại (mô phỏng F5) khôi phục đúng messages + working set + trạng thái mở. **DoD:** khẳng định trên DOM **và** trên payload của câu hỏi kế tiếp. (P2, phụ thuộc 2.2)
- [x] 5.7 `ChatWidget.persistence.test.tsx`: unmount giữa lúc stream ⇒ blob không chứa text tạm; mount lại hiện bong bóng gián đoạn + nút Thử lại. **DoD:** khẳng định trực tiếp trên nội dung `sessionStorage` (bất biến C). (P2, phụ thuộc 3.2)
- [x] 5.8 `ChatWidget.persistence.test.tsx`: bấm Thử lại ⇒ đúng **một** bong bóng câu hỏi, một lần gọi `streamChat`. **DoD:** đỏ với bản `retryLast()` cũ (design D7). (P2, phụ thuộc 3.3)
- [x] 5.9 `ChatWidget.persistence.test.tsx`: "Cuộc trò chuyện mới" xoá sạch và panel vẫn mở; mount lại sau đó vẫn trống. **DoD:** 2 assertion. (P2, phụ thuộc 4.2)
- [x] 5.10 Chạy lại toàn bộ test frontend chat sẵn có (`ChatWidget.streaming` / `.workingset` / `.drift`, `chatAnswer.boundary`, `api/__tests__/chatStream`). **DoD:** xanh, không sửa test cũ để làm xanh — nếu một test cũ đỏ thì đó là hồi quy thật. (P2, phụ thuộc 4.2)

## 6. Kiểm chứng thủ công & docs

- [x] 6.1 Chạy app thật: hỏi 3 lượt có citation → F5 → khẳng định hội thoại, chip working set và trạng thái panel còn nguyên, rồi hỏi tiếp một câu nhắc lại tin cũ để xác nhận ghim vẫn chạy. **DoD:** ghi lại kết quả quan sát vào `measurement.md` của change. (P2, phụ thuộc 5.10)
- [x] 6.2 Kiểm hai tab: hỏi khác nhau ở hai tab, khẳng định không tab nào thấy luồng của tab kia; đóng một tab không ảnh hưởng tab còn lại. **DoD:** ghi kết quả. (P2, phụ thuộc 6.1)
- [x] 6.3 Kiểm F5 giữa lúc câu trả lời đang chảy: khẳng định thấy bong bóng gián đoạn, Thử lại chạy được, và `chat_logs` vẫn có dòng của lượt bị bỏ dở (bất biến D5 của `chat-streaming-sse` không bị change này phá). **DoD:** truy vấn `chat_logs` xác nhận. (P2, phụ thuộc 6.1)
- [x] 6.4 Cập nhật `CLAUDE.md`: ghi bất biến "luồng hội thoại thuộc về tab, không thuộc về ngữ cảnh", khoá `radar-chat-v1`, luật vứt-khi-lệch-phiên-bản, và lý do không lưu `searchSuggestions`. **DoD:** người đọc sau biết vì sao khoá phải phẳng mà không phải đọc lại design. (P2, phụ thuộc 6.3)
