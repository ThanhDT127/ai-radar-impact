> Thứ tự bắt buộc: schema → context thuần → service → frontend → bộ đo → docs.
> Lý do: `build_context()` là hàm thuần mà RS harness phụ thuộc; sửa nó trước khi sửa service
> để bộ đo miễn phí luôn chạy được ở mọi bước.
>
> **Cổng cuối cùng là `chat_answer_harness --live`.** RS đo truy hồi, KHÔNG đo việc model có bị
> 3 dòng tin cũ kéo lạc đề hay không.

## 1. Hợp đồng dữ liệu

- [x] 1.1 Thêm `insight_id: UUID | None` vào `TurnCitation` (`backend/app/schemas/chat.py`), mặc định `None`. **DoD:** client cũ không gửi trường này vẫn parse được, không lỗi 422.
- [x] 1.2 Viết lại ghi chú docstring của `TurnCitation` — nó đang nói "không mang `insight_id`… là bề mặt tấn công". Ghi rõ vì sao ranh giới tin cậy KHÔNG đổi (xem design D6): `referenced_insight_ids` đã nhận id từ client, và id vẫn phải tra ra insight `published` + `is_primary` thật. **DoD:** người đọc sau không tưởng đây là nới lỏng bảo mật.
- [x] 1.3 Thêm `chat_history_pin_slots: int = 3` vào `backend/app/config.py`, kèm chú thích luật "đổi số này ⇒ bắt buộc chạy lại RS harness". **DoD:** `0` là giá trị hợp lệ và nghĩa là tắt.

## 2. Dựng context (hàm thuần)

- [x] 2.1 Thêm tham số `pinned: list[Insight]` vào `build_context()` (`app/services/chat_grounding.py`), mặc định `[]`. **DoD:** hàm vẫn THUẦN — không DB, không model, không đọc `settings`; RS harness chạy offline không đổi một dòng.
- [x] 2.2 Khử trùng `pinned` theo `insight.id` với ô sâu và với tin đã có trong index (design D5). **DoD:** một insight không bao giờ nhận hai số `[n]`.
- [x] 2.3 Ghim **trong** `index_limit`: sau khi lấp ô sâu và cắt top-K, thay N tin ở **đuôi** bằng tin ghim còn lại. **DoD:** tổng số tin vào prompt vẫn đúng `index_limit`, không phình.
- [x] 2.4 Đặt tin ghim ở **cuối** index block (design D4). **DoD:** mọi tin xếp hạng đứng trước mọi tin ghim; dãy `[n]` liên tục, không đứt.
- [x] 2.5 Xác nhận đường `expanded` (`build_index_block(start=2)`) vẫn nối đúng dãy. **DoD:** không sinh không gian số thứ hai.

## 3. Service

- [x] 3.1 Thêm helper trích định danh insight từ `history` theo **thứ tự nhắc gần nhất** (lượt mới trước), khử trùng, cắt ở `chat_history_pin_slots`. **DoD:** tất định — cùng history cho cùng kết quả, không phụ thuộc câu hỏi.
- [x] 3.2 Nạp các insight đó qua **đúng** đường lọc của `_load_refs` (`published` + `is_primary`), bỏ lặng lẽ id không phân giải được. **DoD:** không mở đường nạp thứ hai; id rác không gây lỗi.
- [x] 3.3 Truyền `pinned` vào `build_context()` trong `_answer_global`, áp cho cả ba ca (toàn cục · working set · mở rộng). **DoD:** một đường code, không rẽ nhánh theo mode.
- [x] 3.4 Xác nhận `_rank`, `_relevance`, `_question_terms`, RRF **không bị đụng**. **DoD:** `git diff` không chạm các hàm này.

## 4. Frontend

- [x] 4.1 `ChatTurn.citations` gửi kèm `insight_id` (`frontend/src/api/chat.ts` + `ChatWidget.tsx`) — dữ liệu đã có sẵn trong `Citation`, chỉ là đang bị lược khi dựng history. **DoD:** payload lượt sau mang đủ `{n, title, insight_id}`.
- [x] 4.2 Test: history mang định danh nguồn qua nhiều lượt. **DoD:** thêm ca vào `ChatWidget.drift.test.tsx`, xanh.

## 5. Test cơ chế (miễn phí)

- [x] 5.1 `tests/test_chat_history_pinning.py`: tin đã trích rơi khỏi top-K vẫn có mặt trong index.
- [x] 5.2 Test khử trùng: tin vừa được trích vừa còn trong top-K nhận đúng MỘT số.
- [x] 5.3 Test khử trùng với working set: tin ở ô sâu không bị ghim lại vào index.
- [x] 5.4 Test trần: ghim N chỗ vẫn cho đúng `index_limit` tin vào prompt.
- [x] 5.5 Test thứ tự: mọi tin ghim đứng sau mọi tin xếp hạng.
- [x] 5.6 Test tắt: `chat_history_pin_slots = 0` cho index **trùng khít** bản chưa có change.
- [x] 5.7 Test suy giảm êm: history không kèm `insight_id` (client cũ) → không ghim, không lỗi.
- [x] 5.8 Test biên: id không tồn tại / trỏ insight chưa `published` → bỏ qua lặng lẽ.

## 6. Cổng đo

- [x] 6.1 Chạy `python -m tests.eval.chat_rank_harness`. **DoD:** recall@K = **0,968** và recall@5 = **0,900**, trùng baseline. Ghim là bước SAU xếp hạng nên số phải trùng khít — lệch nghĩa là đã vô tình đụng `_rank`.
- [x] 6.2 Chạy lại phép đo trôi ngữ cảnh (ma trận 6×6 chủ đề). **DoD:** tỉ lệ rơi khỏi index giảm từ **52%** xuống 0% cho N tin gần nhất; ghi số vào `measurement.md`.
- [x] 6.3 Chạy `python -m tests.eval.chat_answer_harness --live`. **DoD:** Faith **≥ 0,95** và CitPrec **= 1,00** (cổng cứng); AnsRel trong ± 0,05 so baseline 0,94–0,95. Đây là lưới DUY NHẤT bắt việc model lạc đề vì tin cũ.
- [x] 6.4 ~~Nếu AnsRel tụt quá dung sai: giảm 3 → 2~~ — **KHÔNG kích hoạt**: AnsRel 0,96 (baseline 0,94–0,95), Faith 0,98, CitPrec 1,00. Giữ 3 chỗ ghim.
- [x] 6.5 Đo độ trễ qua `/chat/stream` với client ẤM, so mốc 29/07 (TTFT toàn cục 3,22s · chốt 4,79s). **DoD:** không hồi quy quá nhiễu; ghi điều kiện đo (client singleton) vào kết quả.

## 7. Tài liệu

- [x] 7.1 Viết `measurement.md` cho change: 52% → sau khi ghim, bảng RS theo K (57/55/54/53), vách hạng 54, và giới hạn "một điểm dữ liệu trên corpus 179 tin".
- [x] 7.2 Cập nhật CLAUDE.md mục chat: bất biến đã **thu hẹp** thành "N tin trích gần nhất"; luật "đổi `chat_history_pin_slots` ⇒ chạy lại RS"; tin ghim vào index chứ không vào ô sâu.
- [x] 7.3 Ghi vào `docs/ignored/chatbot_tobe_conformance.md`: hạng mục "History Summarization" chuyển từ *chưa làm* sang **bác bỏ có lý do đo được** (history = 3,8% prompt; nén làm ca đã đo tệ hơn), và thêm dòng cho cơ chế ghim.
- [x] 7.4 Ghi 3 câu hỏi mở của design vào chỗ tra cứu được, đặc biệt: `MAX_HISTORY_TURNS = 10` là 10 **tin nhắn** = 5 lượt hỏi–đáp, không phải 10 lượt như bản To-Be viết.
