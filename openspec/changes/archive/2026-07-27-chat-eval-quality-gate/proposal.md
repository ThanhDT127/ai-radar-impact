# Proposal: chat-eval-quality-gate

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — phủ phần 6 khung To‑Be: Evaluation & Quality Gate).

## Why

`chat-rank-stability` (RS) đo **một** trong ba cạnh RAG Triad — Context Relevance (recall của `_rank`) — và
cố ý dừng ở đó vì đó là hàm thuần, đo được **không cần model** (RS design D1). Hai cạnh còn lại của Triad
trong báo cáo To‑Be (mục 3.2 #6) **chưa ai đo**:

- **Faithfulness** — câu trả lời có 100% căn cứ từ context, 0% chém gió.
- **Answer Relevance** — câu trả lời có giải quyết đúng câu hỏi.

Cả hai đo **câu trả lời model đẻ ra**, nên bắt buộc sinh câu trả lời **live** rồi chấm — không fixture cứng
được như insight. Không có bộ đo này thì mọi thay đổi prompt/model của chat (kể cả sentinel của
`chat-scope-routing`, hay nâng SDK) đều **không có lưới** bắt hồi quy chất lượng trả lời — đúng hoàn cảnh đã
sinh ra `gate-benchmark-durability` và RS, lặp lần thứ ba.

## What Changes

- **Bộ đo chất lượng câu trả lời chat** — capability mới `chat-answer-eval-harness`, dựng theo mẫu
  `gate-eval-harness`: fixture ~50 kịch bản trong repo, chế độ **`--live`** đo thật (~vài xu), snapshot để
  chạy offline; **không** nằm trong `pytest` mặc định (vì gọi model), khác RS ở đúng điểm này.
- **Chấm kết hợp (a)+(b) — chốt 23/07/2026**:
  - **(a) LLM‑judge** cho **Faithfulness** và **Answer Relevance**: sinh câu trả lời bằng pipeline chat thật
    rồi một model chấm từng khẳng định có được context bảo chứng không / có đúng ý hỏi không.
  - **(b) Structural, 0 model** cho **Citation Precision**: mọi marker `[n]` trỏ đúng insight có thật trong
    index đã phục vụ; không citation bịa.
- **Ngưỡng gate** (từ báo cáo): **Faithfulness ≥ 0,95**, **Citation Precision = 1,00**; **Answer Relevance**
  đóng băng baseline kèm dung sai, báo cáo per‑kịch‑bản.
- **Bộ 50 kịch bản** phủ cả mode A, mode B, và mở rộng (`chat-scope-routing`), mở rộng từ bộ câu của RS.

## Capabilities

### New Capabilities
- `chat-answer-eval-harness`: bộ đo Faithfulness + Answer Relevance (LLM‑judge, live) + Citation Precision
  (structural) cho câu trả lời chat; fixture 50 kịch bản, ngưỡng gate, baseline đối chiếu được.

### Modified Capabilities
_(không có)_

## Non-goals

- **Không** thay RS: Context Relevance vẫn do RS đo (thuần, miễn phí); ④ **tái dùng**, không viết lại.
- **Không** nằm trong `pytest` mặc định — gọi model, tốn tiền, không tất định (giống gate, khác RS).
- **Không** dựng CI pipeline (repo chưa có CI): ④ cấp **lệnh chạy + ngưỡng gate tường minh**; nối vào CI
  hoãn cùng với open question của RS.
- **Không** đổi code sản phẩm của chat — ④ chỉ **đo**, không sửa prompt/service/widget.

## Dependencies

- **`chat-rank-stability` (RS) — land trước**: tái dùng fixture corpus + mẫu harness; ④ đo cạnh Triad còn
  lại, RS đo Context Relevance.
- **`chat-citation-integrity` (CI)**: CI làm citation đúng **bằng cấu trúc**; ④ **đo** Citation Precision —
  ④ là lưới bắt nếu bất biến đó vỡ.
- `gate-eval-harness` (archive 21/07/2026) — mẫu kiến trúc `--live`/offline/baseline.
- `chatbot-qa` (archive 22/07/2026) — pipeline câu trả lời được đo thuộc change đó.

## Impact

- **Backend/Test**: `tests/eval/` — fixture 50 kịch bản, harness live (sinh câu trả lời + LLM‑judge) +
  structural citation check, baseline; script sinh fixture giữ làm bằng chứng xuất xứ.
- **AI/LLM**: hai tầng gọi model khi `--live` — (1) sinh câu trả lời (pipeline thật), (2) judge. Prompt judge
  giữ output **ngắn, có biên** để tránh runaway.
- **Docs**: `CLAUDE.md` — thêm dòng "chạy lại eval chất lượng khi sửa prompt/model chat", song song dòng gate.
- **Không** endpoint, không migration, không đụng frontend.
