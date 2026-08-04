> **Thứ tự bắt buộc: lưới đo → khung tắt → đo quyết định → bật.**
> Nhóm 1–2 land được **độc lập** và có giá trị dù change này bị huỷ: hiện **0/98** kịch bản mang
> `history`, nên không lưới nào canh đường hội thoại đa lượt.
>
> ⚠️ **Cổng sinh tử là 4.2.** Nếu số hạng RRF bổ sung **không** giữ được phần thắng, change
> **DỪNG** và ghi lại kết quả âm. KHÔNG được nới sang "thay vector khi tự tin" — đó chính là
> phương án đã đo được là hạng 1 → 79.

## 1. Lưới đo — bộ kịch bản (land trước, độc lập)

- [x] 1.1 (P2) Thêm trường lịch sử vào schema kịch bản: câu hỏi lượt trước + nguồn đã trích lượt đó. **DoD:** kịch bản không khai báo trường này cho kết quả **trùng khít** cách đo cũ; 98 kịch bản hiện có không đổi một chữ số.
- [x] 1.2 (P2) Đưa 14 kịch bản nhóm `followup_new_topic` vào `tests/eval/chat_scenarios.jsonl` (đang ở scratchpad). Mỗi ca giữ `label_reason` đọc được. **DoD:** mỗi `must_have` neo vào insight có thật trong `chat_corpus.jsonl`.
- [x] 1.3 (P2) Kiểm bất biến định nghĩa nhóm khi nạp: `must_have ∩ turn1_cited = ∅`, vi phạm thì **nổ** kèm tên kịch bản. Dep: 1.2. **DoD:** cố tình làm bẩn một nhãn ⇒ harness đỏ với thông báo đọc được, không phải chấm điểm im lặng.
- [x] 1.4 (P2) Sinh vector câu hỏi cho 14 kịch bản mới qua `build_fixture_chat --top-up`. Dep: 1.2. **DoD:** `--top-up` chứ **không** phải bản không cờ — bản đó ghi đè `chat_corpus.jsonl` bằng DB hiện tại và làm mọi baseline mất tính so sánh.
- [x] 1.5 (P2) Sinh thứ hạng đoạn cho 14 kịch bản mới. Dep: 1.4. **DoD:** `load_chunk_ranks` không báo thiếu mục nào.

## 2. Lưới đo — baseline khi CHƯA có cơ chế

- [x] 2.1 (P2) Chạy `python -m tests.eval.chat_rank_harness`, chốt baseline có nhóm mới. Dep: 1.5. **DoD:** nhóm `followup_new_topic` cho recall@5 **0,786** · recall@60 **1,000** · hạng xấu nhất **29**; điểm của 98 kịch bản cũ **không đổi một dòng nào** (nhóm mới chỉ thêm dòng, không đụng `_rank`).
- [x] 2.2 (P2) Ghi `measurement.md`: bảng 4 cấu hình, phần tự soát rò đáp án (3/14, số bảo thủ 0,727 → 1,000), ĐÍNH CHÍNH task_type, và hai cổng đã chết (`_ANAPHORA_TOKENS` 44,6%/18,9%; `df_min` 7,2%/16,7%). Dep: 2.1. **DoD:** người đọc sau dựng lại được kết luận mà không phải chạy lại.
- [x] 2.3 (P2) Ghi vào `chat_rank_baseline.json` phần meta: nhóm này đo **năng lực truy hồi thuần**, cơ chế ghim cố ý không che nó. **DoD:** không ai đọc nhầm điểm thấp thành hồi quy.

## 3. Backend — khung, mặc định TẮT ⟨ĐÃ CÀI RỒI GỠ 31/07⟩

> Cài xong, dùng để chạy cổng 4.2, rồi **gỡ** sau khi 4.2 cho kết quả âm. Giữ dấu [x] vì
> việc đã làm thật và số đo đến từ nó; xem `measurement.md` §11.3 cho bảng những gì đã gỡ.

- [x] 3.1 (P2) `CHAT_QUERY_REWRITE_ENABLED: bool = False` + `CHAT_QUERY_REWRITE_MODEL_ID` vào `config.py`. **DoD:** tắt là mặc định; chú thích ghi luật "đổi ⇒ chạy lại RS harness".
- [x] 3.2 (P2) `_rank()` nhận thêm một vector truy vấn tuỳ chọn và cộng số hạng RRF thứ tư. Dep: 3.1. **DoD:** `_rank` vẫn là **hàm THUẦN** (không DB, không model, không đọc `settings`) — RS harness offline chạy không đổi một dòng.
- [x] 3.3 (P2) Vector bổ sung là `None` ⇒ **bỏ hẳn** số hạng, không cho mượn thứ hạng nào. Dep: 3.2. **DoD:** thứ tự **trùng khít** bản ba tín hiệu, so bằng test chứ không bằng mắt.
- [x] 3.4 (P2) Tách cổng "rỗng từ khoá" thành áp **riêng từng chuỗi**. Dep: 3.2. **DoD:** câu hỏi rỗng từ khoá vẫn không tốn lượt embed cho chính nó, nhưng KHÔNG kéo theo việc vứt vector bản viết lại.
- [x] 3.5 (P2) Thứ hạng đoạn cho lượt có viết lại: chốt lấy theo chuỗi nào và ghi lý do tại chỗ. Dep: 3.4. **DoD:** một luật duy nhất, không rẽ nhánh ngầm theo mode.

## 4. Đo quyết định (cổng sinh tử)

- [x] 4.1 (P2) Sinh chuỗi viết lại cho 14 kịch bản + embed, đông lạnh vào fixture kèm dấu vân tay (model id + phiên bản prompt); `load_*` **nổ** khi lệch. Dep: 3.5. **DoD:** chạy lại harness khi không có mạng vẫn cho kết quả tất định.
- [x] 4.2 (P2) ⛔ **KẾT QUẢ ÂM — CHANGE DỪNG TẠI ĐÂY.** off r@5 **0,79** · add **0,71** ▼ · replace 0,79 =. Phương án đề xuất làm recall@5 TỆ ĐI. Chi tiết + nguyên nhân: `measurement.md` §11. **Đo ba dạng** trên nhóm `followup_new_topic`: (a) tắt, (b) **cộng** số hạng thứ tư, (c) **thay** vector gốc. Dep: 4.1. **DoD:** có bảng ba cột. Nếu (b) không kéo recall@5 lên rõ so với (a) ⇒ **DỪNG change**, ghi kết quả âm vào `measurement.md`, không đi tiếp.
- [x] 4.3 (P2) Đo tác dụng phụ của (b) trên **toàn bộ** kịch bản cũ. Dep: 4.2. **DoD:** 98 kịch bản không có `history` ⇒ không kích hoạt viết lại ⇒ recall@K **0,968** và recall@5 **0,900** trùng khít. Lệch = có đường rò.
- [x] 4.4 (P2) ✅ Phủ bởi 4.2: cột `replace` chính là ca xấu nhất (bản viết lại chiếm chỗ vector gốc) và nó KHÔNG tốt hơn `off` — nên `replace` bị loại lần thứ hai. Đo giá của viết lại **sai**: tiêm chủ đề lệch, so (b) với (c). Dep: 4.2. **DoD:** chứng minh bằng số rằng (b) chịu được ca sai — mốc đối chứng là (c) làm hạng 1 → 79.

## 5. AI pipeline — lượt viết lại ⟨ĐÃ CÀI RỒI GỠ 31/07⟩

- [x] 5.1 (P2) Prompt viết lại trong `app/ai/prompts.py`: độc lập hoá câu hỏi từ lịch sử, **không** trả lời, **không** thêm thông tin ngoài lịch sử. **DoD:** KHÔNG dùng `response_schema` (bài học `gemini-structured-output`).
- [x] 5.2 (P2) `GeminiClient` thêm lượt viết lại trên model rẻ. Dep: 5.1. **DoD:** lỗi/timeout ⇒ trả `None`, KHÔNG ném ra ngoài; có WARNING.
- [x] 5.3 (P2) Nối vào `_answer_global`: cổng `history` không rỗng, embed bản viết lại, truyền vào `_rank`. Dep: 5.2, 3.4. **DoD:** `history` rỗng ⇒ **0** lượt gọi thêm, đo được bằng test.
- [~] 5.4 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Lượt viết lại + embed **không** cộng vào bộ đếm quota trả lời và **không** cộng vào trần số bước. Dep: 5.3. **DoD:** câu mở rộng có viết lại vẫn đúng 2 bước; quota cạn không đổi hành vi từ chối.
- [x] 5.5 (P2) ✅ Đã xác minh trong lúc cài: đường `insight_id` không bị chạm; sau khi gỡ thì hiển nhiên đúng. Đường `insight_id` (mode B / expanded) **không** đụng tới. Dep: 5.3. **DoD:** `git diff` không chạm nhánh đó.

> ⛔ **Nhóm 5.4 trở đi TREO** — cổng 4.2 cho kết quả âm nên không bật cơ chế. Việc còn lại
> phụ thuộc một quyết định: **giữ khung sau cờ tắt** (⇒ làm nhóm 6 để khoá bất biến
> "tắt = trùng khít") hay **gỡ hẳn** (⇒ revert nhóm 3 và 5, giữ nguyên nhóm 1–2).

## 6. Test cơ chế (miễn phí, trong `pytest` mặc định)

- [~] 6.1 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Tắt bằng cờ ⇒ xếp hạng trùng khít bản chưa có change.
- [~] 6.2 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ `history` rỗng ⇒ không gọi viết lại (dùng client giả **nổ khi bị chạm**).
- [~] 6.3 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Viết lại lỗi ⇒ bỏ hẳn số hạng, vẫn trả lời, có WARNING.
- [~] 6.4 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Embed bản viết lại lỗi ⇒ bỏ hẳn số hạng, **không** thay bằng thứ hạng khác.
- [~] 6.5 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Câu hỏi rỗng từ khoá + bản viết lại có nội dung ⇒ tín hiệu bản viết lại **được giữ**. Đây là ca hỏng im lặng của D5 — không có test này thì cơ chế chết đúng ở ca cần nó nhất.
- [~] 6.6 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Bản viết lại **không** xuất hiện trong prompt gửi model.
- [~] 6.7 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ `_rank` vẫn thuần: gọi được với `session=None` và client giả nổ khi bị chạm.

## 7. Cổng chất lượng (tốn tiền — chạy sau khi 4.2 xanh)

- [~] 7.1 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Bật cờ, chạy `chat_rank_harness`, chốt lại baseline **kèm lý do**. Dep: 4.3. **DoD:** revision ghi rõ số trước/sau và vì sao, theo tiền lệ `chat-hybrid-retrieval`.
- [x] 7.2 (P2) ✅ Đã chạy `--live` cho 14 kịch bản mới (Faith 0,99 · AnsRel 0,89 · CitPrec 1,00), chốt lại baseline kèm lý do. `chat_answer_harness --live`. Dep: 7.1. **DoD:** Faith **≥ 0,95**, CitPrec **= 1,00** (cổng cứng); AnsRel trong ±0,05 baseline. ⚠️ Bộ này **0/98 kịch bản có history** nên nó chỉ chứng minh không hồi quy đường cũ — KHÔNG phải bằng chứng change hoạt động.
- [~] 7.3 (P2) ⟨KHÔNG LÀM — không bật cơ chế thì không có nhánh nào để đo⟩ Đo độ trễ qua `/chat/stream` với **client ẤM** (singleton), có/không viết lại. Dep: 7.1. **DoD:** ghi TTFT hai nhánh và điều kiện đo. Mốc: 2,6–3,9s hiện tại, dự phóng 4,4–6,0s. Đo trên client mới mỗi câu là **thổi phồng ~1,3s**.
- [~] 7.4 (P2) ⟨KHÔNG LÀM — cơ chế đã gỡ⟩ Quyết định bật/tắt mặc định dựa trên 7.2 + 7.3, ghi lý do. **DoD:** nếu độ trễ không chấp nhận được thì giữ mặc định **tắt** và nói rõ — không âm thầm bật.

## 8. Tài liệu

- [x] 8.1 (P2) CLAUDE.md mục chat: số hạng RRF thứ tư; luật "viết lại chỉ nuôi truy hồi, không vào prompt"; luật "đổi prompt viết lại ⇒ sinh lại fixture".
- [x] 8.2 (P2) **Sửa hồ sơ sai**: gỡ cụm "câu nối tiếp được chữa bằng bản gộp‑từ‑khoá tất định" khỏi CLAUDE.md — nó chưa bao giờ tồn tại. **DoD:** grep cụm đó chỉ còn trong change đã archive, kèm đính chính.
- [x] 8.3 (P2) `docs/ignored/chatbot_tobe_conformance.md` mục C2: chuyển khỏi "chưa làm", ghi số đo và kết luận thật (baseline **0,786**, recall@60 **1,000** — nhóm này **không** hỏng nặng).
- [x] 8.4 (P2) Ghi ba câu hỏi mở của design vào chỗ tra cứu được, đặc biệt: **loại B xảy ra bao nhiêu trong lưu lượng thật thì chưa ai biết** — `chat_logs` không lưu `history`.
