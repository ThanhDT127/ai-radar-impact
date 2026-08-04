# Tasks: chat-latency-thinking-budget

**Phase:** 2 (M8 Chatbot). Backend + AI + Test. Không Frontend, không n8n, không migration schema
(trừ cột log tuỳ chọn ở 4.1).

> Thứ tự bắt buộc: nâng SDK và **chứng minh mọi thứ còn chạy** → mới đặt thinking_budget → đo →
> cổng chất lượng. Đảo thứ tự thì khi chất lượng tụt sẽ không biết là do SDK hay do budget.

## 1. Nâng SDK (Backend) — làm trước, chứng minh không vỡ

- [x] 1.1 Nâng `google-genai` 0.8.0 → **1.75.0** trong `requirements.txt`, build lại image backend. **DoD:** container lên được, `import google.genai` OK, in ra version 1.x. ⚠️ Đích ban đầu ghi "2.x" — đo lúc làm: 2.x đòi `pydantic>=2.12.5`, đá nhau với `pydantic==2.9.2` đang pin (pip `ResolutionImpossible`). 1.75.0 là bản cuối nhánh 1.x, chỉ đòi `pydantic>=2.9.0` và ĐÃ có đủ `ThinkingConfig(thinking_budget=...)` ⇒ lên 2.x không mua thêm gì cho mục tiêu này.
- [x] 1.2 Chạy full suite backend. **DoD:** 313 test xanh, 2 skip — bằng đúng số trước khi nâng.
- [x] 1.3 Kiểm tay **cả 6 điểm gọi model** còn chạy đúng trên SDK mới: `gate_analyze`, `analyze`, `chat`, `chat_stream`, `classify_intent`, `embed`. **DoD:** mỗi hàm chạy thật một lần, trả kết quả đúng hình dạng; `chat_stream` vẫn yield nhiều chunk; `embed` vẫn trả 768 chiều.
- [x] 1.4 Xác nhận `usage_metadata.thoughts_token_count` nay có giá trị thật (bản 0.8.0 luôn rỗng). **DoD:** một lượt gọi chat in ra số thinking > 0 và khớp với `total − prompt − candidates`.

## 2. Ghìm ngân sách suy luận (Backend/AI)

- [x] 2.1 `CHAT_THINKING_BUDGET` trong `config.py`, mặc định **256** (design D2). **DoD:** đổi được bằng env, có ghi chú vì sao 256 chứ không 0.
- [x] 2.2 Dựng `ThinkingConfig` ở **một chỗ** dùng chung cho `chat()` và `chat_stream()` (design D3). **DoD:** không có hai chỗ tự dựng config; đọc code thấy ngay hai lối ra không thể trôi khỏi nhau.
- [x] 2.3 Xác nhận `gate_analyze`/`analyze`/`classify_intent` **KHÔNG** nhận thinking config. **DoD:** test khẳng định điều này — nếu ai đó "tiện tay" áp cho cả client thì đỏ.
- [x] 2.4 Xác minh hành vi retry chống-cắt (`chat-answer-completeness`) vẫn đúng khi thinking bị ghìm: thinking nhỏ lại nghĩa là ít chạm `MAX_TOKENS` hơn, nhưng đường hỏi-lại phải còn nguyên. **DoD:** `tests/test_chat_truncation.py` xanh, không phải sửa.

## 3. Cắt độ trễ chuẩn bị ngữ cảnh (Backend)

- [x] 3.1 `_embed_question` ‖ `list_for_chat` bằng `asyncio.gather` (design D4). **DoD:** đo được tổng thời gian chuẩn bị ≈ bước chậm hơn, không phải tổng hai bước.
- [x] 3.2 Câu **rỗng từ khoá** không được gọi embed — bỏ hẳn lượt gọi, không phải gọi rồi vứt (design D4). **DoD:** test: câu "Có gì mới không?" ⇒ 0 lượt embed.

## 4. Làm chi phí thinking nhìn thấy được (Backend)

- [x] 4.1 Ghi `thoughts_token_count` của lượt trả lời vào `chat_logs` (cột nullable + migration 013) và log DEBUG. **DoD:** một lượt chat để lại số thinking đọc được thẳng, không phải suy ra từ hiệu ba số.
- [x] 4.2 Nhà cung cấp không báo cáo số này → ghi NULL, không làm hỏng lượt trả lời. **DoD:** test với response không có trường đó.

## 5. Đo + CỔNG BẮT BUỘC (Test)

- [x] 5.1 Đo độ trễ **trước/sau** trên cùng bộ câu, cùng máy: ít nhất 3 câu tra cứu thường + 1 câu tổng hợp ("tin tuần này"). Ghi bảng. **DoD:** câu thường **≤ 5s**, câu tổng hợp **≤ 8s**; nếu chưa đạt thì dừng và báo, đừng lách bằng cách cắt top-K (non-goal).
- [x] 5.2 `chat_answer_harness --live` **toàn bộ**. **DoD:** Faithfulness ≥ 0,95 **và** Citation Precision = 1,00. Đỏ ⇒ nâng budget 256 → 512 → 1024 rồi đo lại; **KHÔNG hạ ngưỡng** (design D5).
- [x] 5.3 Chốt lại baseline answer-eval kèm lý do + số thinking mới. **DoD:** revision entry ghi rõ budget nào, đo ngày nào.
- [x] 5.4 RS harness phải cho số **Y HỆT** (change này không đụng `_rank`). **DoD:** PASS và recall@60/recall@5 không đổi một chữ số — đổi nghĩa là đã chạm nhầm chỗ, dừng lại điều tra.

## 6. Tài liệu (làm sau khi code đã chạy)

- [x] 6.1 `CLAUDE.md`: nguyên nhân độ trễ THẬT là thinking (kèm số đo), SDK 0.8.0 giấu `thoughts_token_count` nên nó vô hình, núm `CHAT_THINKING_BUDGET` và luật chỉnh nó (gate đỏ thì nâng, không hạ ngưỡng), và **vì sao cắt top-K là sai đường** (60→10 chỉ 17,4s→11,6s, trả bằng recall). **DoD:** người đọc sau này không lặp lại việc cắt top-K để tìm tốc độ.
- [x] 6.2 Cập nhật mục chi phí: thinking bị tính tiền như output ($2,50/1M) nên ghìm budget vừa nhanh hơn vừa rẻ hơn. **DoD:** con số $/câu được đo lại, không chép số cũ.
