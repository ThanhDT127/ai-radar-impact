> Thứ tự bắt buộc: hợp đồng sự kiện → backend phát mốc → frontend render → test.
> Lý do: `key` là tập đóng dùng chung hai phía; định nghĩa nó trước thì mỗi bên sau đó chỉ
> việc bám vào, không phải sửa ngược.
>
> **Change này KHÔNG đụng nội dung câu trả lời** ⇒ không chạy lại RS harness, không chạy
> `chat_answer_harness --live`. Nếu một task nào đó buộc phải sửa `_rank`/`build_context`/
> grounding thì task đó **sai phạm vi** — dừng lại và xem lại design.

## 1. Hợp đồng sự kiện (Backend)

- [x] 1.1 Định nghĩa tập đóng `StatusKey` ở **một chỗ** trong `backend/app/services/chat_service.py`, gồm: `searching`, `ranked`, `pinned`, `reading`, `expanding`, `retrying`, `composing`. **DoD:** không có chuỗi key nào viết rời rạc ở nơi khác; `grep` ra đúng một định nghĩa. (P2)
- [x] 1.2 Thêm `key` vào sự kiện `status` trong `self._status()` — chữ ký thành `_status(key, text)`. **DoD:** mọi call site hiện có truyền `key` tường minh; `emit=None` (blocking) vẫn no-op, không đổi một dòng nào ở `POST /api/v1/chat`. (P2)
- [x] 1.3 Cập nhật schema/tài liệu sự kiện SSE (`backend/app/schemas/chat.py` hoặc nơi mô tả khung SSE) để `key` là trường khai báo, không phải phụ lục. **DoD:** người đọc schema biết được tập key hợp lệ mà không phải đọc service. (P2)

## 2. Phát mốc mới (Backend)

- [x] 2.1 Mốc `ranked`: phát trong `_answer_global` **sau** khi `_rank` trả về, mang số tin khớp và tổng số tin xét (design D4). **DoD:** không phát khi chưa có số thật; câu mode B (không qua `_rank`) không phát mốc này. (P2, phụ thuộc 1.2)
- [x] 2.2 Mốc `pinned`: phát khi tập tin ghim từ history **khác rỗng**, mang tiêu đề tin đầu tiên (rút gọn theo `_STATUS_TITLE_LEN` sẵn có) + số tin còn lại. **DoD:** `chat_history_pin_slots=0` hoặc history rỗng ⇒ không phát; không thêm truy vấn DB nào (dùng lại kết quả `_load_refs` đã nạp). (P2, phụ thuộc 1.2)
- [x] 2.3 Mốc `retrying`: phát khi `GeminiClient.chat`/`chat_stream` phải hỏi lại vì `MAX_TOKENS` (`chat-answer-completeness`). **DoD:** mốc tới **trước** lượt hỏi lại chứ không phải sau; câu không bị cắt thì không bao giờ thấy mốc này. (P2, phụ thuộc 1.2)
- [x] 2.4 Rà lại toàn bộ call site `_status` cũ, gán `key` đúng và kiểm tra không mốc nào bị phát hai lần liên tiếp cho cùng một việc (ghi chú sẵn ở `_answer_global` về `STATUS_EXPANDING` vs `STATUS_SEARCHING`). **DoD:** một lượt không bao giờ phát hai `status` cùng `key` liền nhau. (P2)
- [x] 2.5 Xác nhận không có mốc nào được phát từ trong `build_context()`. **DoD:** hàm vẫn **thuần** — không I/O, không emit; RS harness chạy offline không đổi. (P2)

## 3. Frontend

- [x] 3.1 Đổi state `pending.status: string | null` thành danh sách mốc `{key, text, done}` trong `ChatWidget.tsx`. **DoD:** mốc mới cùng `key` thì **cập nhật tại chỗ**, `key` khác thì **thêm dòng**; `key` lạ vẫn thêm dòng chứ không bị nuốt (design D2). (P2, phụ thuộc 1.2)
- [x] 3.2 Render xếp chồng: mốc đã qua mờ + dấu `✓`, mốc hiện tại đậm + spinner. Trần **4** dòng, vượt thì bỏ dòng cũ nhất (design D3). **DoD:** panel hẹp không tràn ngang; không có thanh tiến trình %. (P2, phụ thuộc 3.1)
- [x] 3.3 Xoá sạch khối status khi `commit` tới, giữ nguyên hành vi hiện nay. **DoD:** không còn dòng mờ nào sót lại cạnh câu trả lời đã chốt. (P2, phụ thuộc 3.1)
- [x] 3.4 Giữ nguyên fallback `'Đang gửi câu hỏi…'` khi chưa có mốc nào. **DoD:** khoảnh khắc đầu tiên sau khi bấm Gửi không bao giờ trống. (P2)
- [x] 3.5 Cập nhật kiểu sự kiện SSE trong `frontend/src/api/chat.ts` cho `key`. **DoD:** `tsc` sạch; bộ đọc khung SSE (đệm tới `\n\n`) **không đổi**. (P2)

## 4. Test

- [x] 4.1 Backend: test thứ tự và tập `key` phát ra cho ba ca — toàn cục, working set (có refs), mode B → expanded. **DoD:** khoá được *mốc nào phát, key gì, thứ tự nào*; đỏ nếu ai đó bỏ một mốc. (P2)
- [x] 4.2 Backend: test đường blocking (`emit=None`) **không** đổi hành vi. **DoD:** `POST /api/v1/chat` trả đúng payload như trước change. (P2)
- [x] 4.3 Backend: test `retrying` chỉ phát khi thật sự có lượt hỏi lại (giả lập `MAX_TOKENS`). **DoD:** ca không cắt ⇒ 0 lần phát. (P2, phụ thuộc 2.3)
- [x] 4.4 Backend: test mốc `pinned` không phát khi `chat_history_pin_slots=0`. **DoD:** đường rollback của `chat-history-pinning` vẫn im lặng đúng. (P2, phụ thuộc 2.2)
- [x] 4.5 Frontend: mở rộng `ChatWidget.streaming.test.tsx` — nhiều `status` khác `key` ⇒ nhiều dòng; cùng `key` ⇒ cập nhật tại chỗ; `key` lạ ⇒ vẫn hiện. **DoD:** 3 test mới, xanh. (P2, phụ thuộc 3.1)
- [x] 4.6 Frontend: test trần 4 dòng và test khối biến mất khi `commit`. **DoD:** xanh. (P2, phụ thuộc 3.2, 3.3)

## 5. Kiểm chứng thủ công & docs

- [x] 5.1 Chạy thật một câu toàn cục và một câu working set trên dashboard, ghi lại **mốc thời gian từng status** (client ấm, singleton — xem cảnh báo đo lường ở `chat-context-depth`). **DoD:** có bảng thời điểm thực tế; xác nhận không có khoảng im lặng nào > ~1,5s. (P2)
- [x] 5.2 Chốt câu hỏi mở của design: có phát `ranked` khi 0 tin khớp không. **DoD:** quyết định ghi vào design.md kèm lý do, không để treo. (P2, phụ thuộc 5.1)
- [x] 5.3 Cập nhật mục Chat trong `CLAUDE.md`: danh sách mốc status, luật "`key` là tập đóng", và ghi rõ **đa dạng đến từ dữ liệu, không từ đồng nghĩa**. **DoD:** người đọc sau không "cải thiện" bằng cách thêm biến thể câu chữ. (P2)
