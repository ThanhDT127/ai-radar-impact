# Tasks: chat-citation-integrity

> Thứ tự: backend → frontend → đo lại → docs. Docs đi **sau cùng** có chủ đích — task 5.3 của
> `chatbot-qa` viết docs trước section 4b rồi không cập nhật lại, và đó chính là nợ đang phải trả ở đây.

## 1. Hợp đồng `n` — backend

- [ ] 1.1 Thêm `n: int` vào `Citation` (`schemas/chat.py`). Chỉ **thêm** trường, không đổi/xoá trường cũ. **DoD:** response `POST /api/v1/chat` mang `n` cho mọi citation.
- [ ] 1.2 `resolve_citations` trả `n` kèm mỗi citation; giữ nguyên số marker trong answer, **KHÔNG** đánh số lại (design D2). **DoD:** với answer `"...[3]...[7]..."` và mapping 60 tin, citations mang `n = 3, 7` và answer vẫn là `[3]`, `[7]`.
- [ ] 1.3 Test backend cho dãy marker không liền mạch: `[3][7][12]`, `[2]` đơn lẻ, `[5]` trước `[2]`. **DoD:** mỗi citation mang đúng `n` và đúng `insight_id` của index tương ứng.
- [ ] 1.4 Rà lại `test_resolve_citations_maps_markers_in_order` — test này đang khoá đúng ca làm widget trỏ sai. Giữ phần khẳng định thứ tự citations, **bổ sung** khẳng định về `n`. **DoD:** test nêu rõ `n` là số index, không phải vị trí mảng.

## 2. Hợp đồng `n` — frontend

- [ ] 2.1 Thêm `n` vào type `Citation` trong `frontend/src/api/chat.ts`.
- [ ] 2.2 `renderAnswer`: giải marker bằng `citations.find(c => c.n === n)` thay cho `citations[n-1]`. Không tìm thấy → render text thường, **tuyệt đối không** rơi sang citation khác. **DoD:** đọc code thấy rõ không còn phép tính chỉ số nào trên `citations`.
- [ ] 2.3 Danh sách nguồn dưới bong bóng hiển thị `[{citation.n}]` thay cho `[{index+1}]` — khớp marker trong câu (design D2, Open Question đã chốt). **DoD:** inline nói `[12]` thì list cũng nói `[12]`.
- [ ] 2.4 Dựng hạ tầng test frontend tối thiểu (repo **chưa có test frontend nào**) — chỉ đủ chạy hàm render thuần, không dựng bộ test toàn diện. **DoD:** `npm test` chạy được, 1 lệnh, không cần trình duyệt.

## 3. Test cắt qua ranh giới

- [ ] 3.1 Test dựng answer + mapping theo đúng logic backend, chạy qua logic render của widget, khẳng định **mọi marker trỏ đúng insight**. Dãy phải phủ: liền từ 1 (`[1][2][3]`), đơn lẻ (`[2]`), có lỗ hổng (`[1][2][4]`), cách quãng (`[1][3][5]`), đảo thứ tự (`[2][1]`), xa (`[3][7][12]`). **DoD:** cả 6 dãy pass; cố tình quay lại `citations[n-1]` thì ít nhất 5/6 fail.
- [ ] 3.2 Ghi vào test một dòng nêu **vì sao** test này tồn tại: test một bên ranh giới không bảo vệ được ranh giới; ca `[2]→B, [1]→A` từng xanh ở backend trong khi widget trỏ sai cả hai.
- [ ] 3.3 Log (DEBUG/INFO, **không** WARNING) khi model phát ra dãy marker không liền mạch từ 1 — tín hiệu sớm cho việc xếp hạng đặt tin lệch vào top (quyết định chốt 22/07). Sau khi sửa thì marker nhảy cóc không còn gây hỏng, nên đây là quan sát chứ không phải lỗi. **DoD:** hỏi mode A vài câu, đọc log thấy được tần suất thật của ca này.

## 4. Độ liên quan khớp theo từ

- [ ] 4.1 `_relevance` so khớp **theo biên từ** thay cho `t in haystack`: tách haystack bằng cùng regex đang dùng cho câu hỏi rồi so tập hợp. Giữ nguyên ngưỡng 2 ký tự và `_STOPWORDS` (design D3). **DoD:** `"ai"` không còn khớp *email/domain/training/detail*; `"mã"`, `"mở"`, `"dữ"` vẫn khớp bình thường.
- [ ] 4.2 Dọn `_STOPWORDS` trùng lặp (`quan`, `gì`, `nên`, `sẽ` xuất hiện 2 lần).
- [ ] 4.3 Chạy lại bộ đo recall của 4b.2 trước/sau, **thêm ca truy vấn `"AI"`** và một ca ASCII ngắn khác (`"ML"`/`"Go"`). **DoD:** recall tổng không tụt dưới mức 91% đã đo; ghi số đo vào change. **Không** dùng bộ 15 câu làm bằng chứng — nó vẫn "đạt" khi recall tụt 42%.

## 5. Dọn nợ

- [ ] 5.1 Bỏ 3 tham số chết `topics`/`roles`/`keyword` của `InsightRepository.list_for_chat` cùng phần SQL tương ứng. Giữ nguyên `published_since` và điều kiện `status="published" AND is_primary`. **DoD:** `test_list_for_chat_filters_primary_and_published` vẫn pass.

## 6. Tài liệu (làm sau khi code đã chạy)

- [ ] 6.1 Sửa `CLAUDE.md:218`: bỏ *"nhét cả corpus"* (thực tế top-K=60), nêu xếp hạng **hai tầng** (relevance → `score_for_role`) chứ không chỉ `score_for_role`, thêm `CHAT_INDEX_TOP_K` vào danh sách env, sửa lời khuyên "hạ 90/30 khi corpus vượt ~1250 tin" cho khớp việc top-K đã làm chi phí phẳng theo corpus.
- [ ] 6.2 Thêm vào `CLAUDE.md` một dòng gotcha về hợp đồng `n`: marker là **số index do server cấp phát**, không phải vị trí trong mảng citations — kèm lý do đừng "tối ưu" thành phép tính chỉ số.
- [ ] 6.3 Sửa `docs/system_overview.md:406` — *"nhét cả kho"* → mô tả đúng cơ chế top-K.
- [ ] 6.4 Đối chiếu lần cuối: mở `CLAUDE.md` mục chat, đọc từng câu, kiểm với code thật. **DoD:** không còn câu nào mô tả trạng thái trước-4b.

## 7. Xác minh bằng mắt

- [ ] 7.1 Chạy dashboard thật, hỏi mode A một câu mà đáp án nằm rải rác (ví dụ "so sánh tin về mã nguồn mở với tin về bảo mật"), **bấm từng marker**, xác nhận mở đúng tin. **DoD:** ghi lại dãy marker model phát ra và kết quả từng lần bấm — bằng chứng bằng ảnh/ghi chú, không phải "tsc pass".
- [ ] 7.2 Lặp lại ở mode B (per-insight) để chắc không hồi quy đường vốn đang đúng.
