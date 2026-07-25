# Tasks: chat-rank-stability

**Phase:** 2 (M8 Chatbot). Toàn bộ là Backend + Test — không đụng Frontend, không migration, không n8n.

> Thứ tự bắt buộc: **fixture → harness → chốt baseline → mới được sửa code**. Chốt baseline sau khi sửa
> thì baseline đã nhiễm thay đổi và mất sạch ý nghĩa. Đây là lý do nhóm 3 nằm sau nhóm 2.
>
> **Luật baseline — áp dụng cho mọi thay đổi xếp hạng về sau:** baseline đầu tiên chốt trên code
> **chưa sửa gì**, tức là trên code còn lỗi (`_relevance` hiện vẫn khớp chuỗi con — `chat-citation-integrity`
> chưa implement). Vì vậy mỗi lần một thay đổi **có chủ đích** làm recall tăng, phải **chốt lại baseline
> ở mức mới**. Không chốt lại thì guard vẫn nằm ở mức cũ thấp hơn, và một lần revert sẽ tụt về đúng
> baseline cũ → **harness pass, lỗi quay lại im lặng**. Đây chính là ca harness sinh ra để chặn.

## 1. Fixture (Test)

- [ ] 1.1 Viết `backend/tests/eval/build_fixture_chat.py` — đọc DB, xuất mọi insight `published` + `is_primary` ra JSONL kèm đủ field mà `_rank()` đọc (danh sách đầy đủ ở design D2). Giữ file lại làm bằng chứng xuất xứ, không dọn. **DoD:** chạy một lệnh sinh ra `chat_rank_benchmark.jsonl`; mở file thấy đủ 14 field cho mỗi mẫu.
- [ ] 1.2 Sinh fixture từ corpus hiện tại (179 insight). **DoD:** số dòng JSONL khớp `SELECT count(*) FROM insights WHERE status='published' AND is_primary`.
- [ ] 1.3 Soạn bộ câu hỏi phủ 6 nhóm ở design D4, mỗi câu ghi `group`. **DoD:** mỗi nhóm (a)–(f) có ít nhất 1 câu; nhóm nào chỉ có 1 câu thì ghi chú rõ là tín hiệu, không phải bằng chứng.
- [ ] 1.4 Gán nhãn `must_have` cho từng câu hỏi bằng cách **đọc tay**, kèm `label_reason` cho mỗi phần tử (theo mẫu `human_reason` của gate). Chỉ chọn tin mà bỏ sót là hỏng rõ ràng — không cố gán hết ca biên. **DoD:** mỗi câu có ≥1 `must_have`; mỗi `must_have` có lý do đọc được, không phải "liên quan".

## 2. Harness + baseline (Test)

- [ ] 2.1 Viết `backend/tests/eval/chat_rank_harness.py`: nạp fixture → rehydrate thành `Insight` ORM **tách rời session** (design D2) → gọi `_rank()` thật → tính recall@`settings.chat_index_top_k`. **DoD:** chạy được khi `docker compose stop db`; không import `database.py`.
- [ ] 2.2 Kiểm tra toàn vẹn fixture lúc khởi động: đối chiếu tập field trong fixture với field mà `_rank`/`score_for_role` thực sự đọc; thiếu thì dừng kèm thông báo rõ. **DoD:** cố tình xoá một field khỏi 1 dòng JSONL → harness dừng và nêu đúng tên field, không đo tiếp.
- [ ] 2.3 Báo cáo in recall **từng câu hỏi** (kèm `group`) bên cạnh recall tổng; mỗi miss nêu đích danh insight bị cắt và thứ hạng thực tế của nó. **DoD:** đọc báo cáo biết ngay câu nào hỏng và tin nào rớt, không cần mở code.
- [ ] 2.4 **Chốt baseline trên code CHƯA sửa gì** — ghi hằng số kèm ngày, theo mẫu `BASELINE_2026_07_21` của gate. **DoD:** hằng số nằm trong harness, có ngày, có comment nêu đo trên commit nào.
- [ ] 2.5 Ngưỡng fail: recall tổng tụt dưới baseline **hoặc** bất kỳ câu nào tụt so với baseline của chính nó, dung sai khai báo tường minh (không so bằng). **DoD:** giả lập tụt 1 câu → harness fail và gọi tên đúng câu đó.
- [ ] 2.6 Wrapper `backend/tests/eval/test_chat_rank_benchmark.py` để chạy trong `pytest` mặc định — **không** skip, vì không gọi model (design D1). **DoD:** `pytest tests/eval/ -q` chạy cả gate lẫn chat; phần chat không phát sinh lần gọi Vertex nào.
- [ ] 2.7 Docstring đầu harness theo mẫu gate: lệnh chạy, **khi nào bắt buộc chạy lại** (`_rank`, `_relevance`, `_question_terms`, `_roles_in_question`, `_STOPWORDS`, `score_for_role`, `chat_index_top_k`), và giới hạn diễn giải (ảnh chụp 22/07/2026, đo hồi quy so với chính nó, không suy sang corpus khác quy mô). **DoD:** đọc riêng docstring đủ biết chạy và đọc kết quả, không phải hỏi ai.

## 3. Sửa `_roles_in_question` (Backend)

> Phụ thuộc: nhóm 2 xong và baseline đã chốt.

- [ ] 3.1 `_roles_in_question` khớp **dãy token liên tiếp** thay cho `role.lower() in question.lower()`; tách token bằng cùng regex `[0-9a-zA-ZÀ-ỹ]+` đang dùng cho từ khoá. Lưu ý vai trò nhiều từ: `Data Analyst` (2 token), `Người dùng phổ thông` (4 token) — không so tập hợp được (design D5). **DoD:** `device`/`DevOps` không còn ra `Dev`; `Dev` đứng riêng vẫn ra; `Data Analyst`, `Người dùng phổ thông` vẫn ra.
- [ ] 3.2 Unit test cho 6 scenario của spec delta `chat-qa-service`. **DoD:** quay lại `role.lower() in question.lower()` thì ít nhất 2 test fail.
- [ ] 3.3 Log DEBUG trục xếp hạng đã chọn ở `_answer_global` (design D5) — mức DEBUG, **không** WARNING: đây là quan sát, không phải lỗi. **DoD:** hỏi vài câu, đọc log thấy được trục thật đang dùng.
- [ ] 3.4 Kiểm lại `empty_roles` không hồi quy — nó dùng chung `asked_roles` nên đổi nhận diện là đổi luôn tuyên bố "không có tin nào cho vai trò X". **DoD:** test khẳng định hỏi "device" không sinh ra tuyên bố về vai trò `Dev`.

## 4. Đo lại (Test)

- [ ] 4.1 Chạy harness trước/sau nhóm 3, ghi số vào change. Nếu recall tăng thì **chốt lại baseline ở mức mới** (luật baseline ở đầu file), kèm lý do. **DoD:** có bảng recall trước/sau theo từng câu; câu nào đổi thì giải thích được vì sao; baseline trong harness khớp số "sau".
- [ ] 4.2 Kiểm chứng harness thật sự nhạy với loại lỗi nó sinh ra để chống. Lưu ý `_relevance` **hiện đang là** so khớp chuỗi con, nên phép thử đi theo chiều ngược: tạm sửa `_relevance` sang khớp biên từ (bản nháp của `chat-citation-integrity` 4.1) → chạy harness → recall nhóm câu ASCII ngắn **phải đổi rõ rệt**. Hoàn tác sau khi xác nhận, **không** commit bản nháp này. **DoD:** ghi lại số trước/sau của riêng nhóm ASCII ngắn; nếu **không đổi** thì bộ câu hỏi chưa phủ được chế độ hỏng — quay lại 1.3, đừng đi tiếp.

## 5. Bàn giao cho `chat-citation-integrity`

- [ ] 5.1 Thay task 4.3 của `openspec/changes/chat-citation-integrity/tasks.md` bằng task mới dùng harness này, gồm **ba** phần: (a) chạy harness trước/sau khi sửa `_relevance`, (b) ghi số theo từng câu, (c) **chốt lại baseline ở mức mới**. Phần (c) là bắt buộc — thiếu nó thì guard vẫn nằm ở mức code-còn-lỗi và một lần revert 4.1 sẽ lọt qua harness (luật baseline ở đầu file). **DoD:** change kia không còn cam kết đo mà không có công cụ đo, và có bước chốt lại baseline.
- [ ] 5.2 Thêm `chat-rank-stability` vào mục Dependencies của `chat-citation-integrity/proposal.md`, nêu rõ phải land trước task 4.1. **DoD:** đọc proposal kia biết thứ tự bắt buộc.
- [ ] 5.3 Đối chiếu vùng code hai change đụng tới: change này **chỉ** `_roles_in_question`, change kia **chỉ** `_relevance`/`_question_terms` (design "Risks"). **DoD:** xác nhận không chồng lấn dòng nào.

## 6. Tài liệu (làm sau khi code đã chạy)

- [ ] 6.1 Thêm gotcha vào `CLAUDE.md` mục chat: benchmark xếp hạng là thứ **duy nhất** bắt được hồi quy `_rank`, kèm lệnh chạy — viết song song với dòng đã có cho `GATE_PROMPT`. **DoD:** copy lệnh trong `CLAUDE.md` chạy được ngay, không phải sửa.
- [ ] 6.2 Ghi vào `CLAUDE.md` bẫy `_roles_in_question`: nhận diện vai trò khớp theo biên từ, đừng "tối ưu" về `in` chuỗi — kèm ca `device`→`Dev` làm ví dụ cụ thể. **DoD:** người đọc hiểu vì sao không được đơn giản hoá chỗ này.
