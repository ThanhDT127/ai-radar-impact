# Tasks: chat-eval-quality-gate

**Phase:** 2 (M8 Chatbot). Thuần Test/Eval + Docs — không đụng code sản phẩm, không migration, không n8n.

> Phụ thuộc: **`chat-rank-stability` land trước** (tái dùng fixture corpus + mẫu harness). Cấu trúc bám
> `gate-eval-harness`: fixture tự chứa, `--live` đo thật, offline chạy lại, baseline đóng băng.

## 1. Fixture 50 kịch bản (Test)

- [x] 1.1 Soạn ~50 kịch bản mở rộng từ bộ câu RS: mỗi kịch bản ghi `mode` (A/B/expanded), câu hỏi, và **tập insight đáng lẽ được cite** gán tay (tái dùng `must_have` của RS khi trùng), kèm `label_reason`. **DoD:** ≥50 kịch bản; phủ đủ A, B, và câu **mở rộng** (out‑of‑scope của `chat-scope-routing`).
- [x] 1.2 Script sinh phần corpus của fixture (tái dùng của RS nếu có), giữ lại làm bằng chứng xuất xứ. **DoD:** một lệnh dựng lại được fixture; không dọn script.

## 2. Harness sinh + chấm (Test)

- [x] 2.1 Chế độ `--live`: mỗi kịch bản chạy **pipeline chat thật** để sinh câu trả lời + citations, lưu snapshot. **DoD:** `--live` sinh ra file snapshot cho cả 50 kịch bản; đếm được số lượt gọi model đã dùng.
- [x] 2.2 **Faithfulness (LLM‑judge)**: judge chấm từng khẳng định trong câu trả lời có được context (tin đã cite) bảo chứng không; verdict **đóng khung ngắn** (supported/partial/not‑supported), nhiệt độ thấp (design D3). **DoD:** ra điểm Faithfulness per‑kịch‑bản; judge không sinh output dài tự do.
- [x] 2.3 **Answer Relevance (LLM‑judge)**: chấm câu trả lời có giải quyết đúng câu hỏi. **DoD:** điểm Answer Relevance per‑kịch‑bản.
- [x] 2.4 **Citation Precision (structural, 0 model)**: mọi marker `[n]` trong câu trả lời trỏ đúng insight thật trong index đã phục vụ; đếm citation bịa. **DoD:** đo được không gọi model; một citation trỏ sai/bịa làm điểm < 1,00.
- [x] 2.5 Chế độ offline: chấm lại trên snapshot đã lưu, **không** gọi pipeline sinh (design D2). **DoD:** chạy offline không phát sinh lượt sinh câu trả lời; ghi rõ trong báo cáo đây là snapshot, không phải đo pipeline hiện tại.

## 3. Gate + baseline (Test)

- [x] 3.1 Ngưỡng gate hard: **Faithfulness ≥ 0,95**, **Citation Precision = 1,00**; Answer Relevance đóng băng baseline + dung sai (design D1, D5). **DoD:** một lệnh cho verdict PASS/FAIL theo đúng ngưỡng.
- [x] 3.2 Baseline đóng băng (`--live`) kèm ngày, per‑kịch‑bản, theo mẫu gate/RS. Cập nhật baseline là hành động có chủ đích kèm lý do, không phải để test xanh. **DoD:** hằng số baseline có ngày + commit đo.
- [x] 3.3 Báo cáo per‑kịch‑bản (kèm `mode`, `group`): một loại câu vỡ không được chìm trong trung bình (bài học RS D7). **DoD:** đọc báo cáo biết ngay kịch bản nào tụt và tụt cạnh nào (Faith/AnsRel/CitPrec).
- [x] 3.4 Docstring đầu harness: lệnh chạy, chi phí thật (điền sau lần `--live` đầu), **khi nào bắt buộc chạy lại** (`CHAT_SYSTEM_PROMPT`, prompt mode B / sentinel của `chat-scope-routing`, đổi model/SDK), và giới hạn diễn giải. **DoD:** đọc riêng docstring đủ chạy và đọc kết quả.

## 4. Tài liệu (làm sau khi đã đo `--live` một lần)

- [x] 4.1 `CLAUDE.md` mục chat: eval chất lượng câu trả lời là lưới **duy nhất** bắt hồi quy Faithfulness/Answer‑Relevance; nêu (a) LLM‑judge cho hai cạnh này + (b) structural cho Citation Precision; ngưỡng gate; lệnh chạy — song song dòng đã có cho gate và RS. **DoD:** copy lệnh chạy được ngay.
- [x] 4.2 Ghi rõ ranh giới với RS: RS đo Context Relevance (thuần, miễn phí, trong `pytest`); ④ đo hai cạnh còn lại (gọi model, tốn tiền, ngoài `pytest`). **DoD:** người đọc không nhầm chạy cái nào khi nào.
