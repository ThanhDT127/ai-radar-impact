# Tasks: chat-context-isolation

**Phase:** 2 (M8 Chatbot). Toàn bộ Frontend + Test — không đụng Backend, không migration, không n8n.

> Thứ tự: dựng test runner → viết ca drift (đỏ) → sửa widget cho xanh → docs. Viết ca drift **trước** khi
> sửa để chắc test thật sự bắt được lỗi đang có, không phải viết sau cho khớp bản đã sửa.

## 1. Hạ tầng test frontend (Test)

- [x] 1.1 Dựng test runner tối thiểu cho frontend (repo **chưa có test frontend nào**): một lệnh `npm test`, chạy headless, không cần trình duyệt. Chỉ đủ để test hàm/logic thuần và state của widget. **DoD:** `npm test` chạy xanh với 1 test placeholder; không thêm bộ test E2E/trình duyệt.
- [x] 1.2 Điều phối với `chat-citation-integrity` task 2.4: change nào land trước thì task 1.1 này dựng runner, change sau bỏ phần dựng và chỉ thêm test. Ghi rõ trong PR change nào đã dựng. **DoD:** không có hai lần cấu hình runner trùng nhau trong repo.

## 2. Cô lập hội thoại theo scope (Frontend)

- [x] 2.1 Thay `messages: Message[]` bằng luồng‑theo‑scope: `scopeKey = activeInsightId ?? "__global__"` (design D2), lưu `Record<scopeKey, Message[]>`. Widget render luồng của `scopeKey` hiện tại. **DoD:** đổi bài A→B đổi luồng hiển thị; quay lại A thấy lại luồng A (design D1).
- [x] 2.2 `send()` dựng `history` từ **luồng của scope hiện tại**, không phải từ toàn bộ hội thoại phiên. Giữ nguyên việc bỏ bong bóng lỗi. **DoD:** đọc code thấy `history` lấy theo `scopeKey`; không còn `messages.filter(...)` trên mảng gộp toàn phiên.
- [x] 2.3 Bỏ chip (✕) và rời detail đều đổi `scopeKey` sang `"__global__"` → mở luồng toàn cục sạch (design D3, D2). **DoD:** bấm ✕ khi đang ở bài rồi hỏi → `insight_id` vắng và `history` không chứa lượt về bài đó.
- [x] 2.4 Đóng/mở panel **không** mất luồng nào (giữ đúng requirement "không mất hội thoại trong phiên" đang có). **DoD:** hỏi ở A, đóng panel, mở lại ở A → luồng A còn nguyên.

## 3. Test drift (Test)

- [x] 3.1 Ca A→B→A: hỏi ở scope A, chuyển sang B, khẳng định payload gửi ở B có `history` **không** chứa lượt của A; quay lại A khẳng định luồng A còn. **DoD:** test đỏ trên code hiện tại (`messages` gộp), xanh sau nhóm 2.
- [x] 3.2 Ca bỏ chip: đang ở bài, bấm ✕, hỏi — khẳng định `insight_id` vắng **và** `history` không chứa lượt về bài. **DoD:** test bắt đúng "Xung đột Mức 2" của Scope Paradox.
- [x] 3.3 Ca rời detail về danh sách: hỏi ở bài, điều hướng về `/`, hỏi — `history` là luồng toàn cục, không phải luồng bài. **DoD:** test khẳng định trên payload gửi đi, không trên DOM.
- [x] 3.4 Ghi một dòng trong test nêu **vì sao** nó tồn tại: history gộp xuyên scope là Nguy hiểm #3; test khoá bất biến "history theo scope". **DoD:** đọc test hiểu ngay lỗi nó chống.

## 4. Tài liệu (làm sau khi code đã chạy)

- [x] 4.1 Thêm gotcha vào `CLAUDE.md` mục chat: `history` widget gửi lên **phải** cô lập theo scope (`insight_id` hoặc toàn cục); gộp xuyên scope gây context poisoning, đã có test chặn. **DoD:** người đọc hiểu vì sao không được "gộp cho tiện".
