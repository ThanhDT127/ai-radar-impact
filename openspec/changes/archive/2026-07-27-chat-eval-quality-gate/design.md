## Context

Báo cáo To‑Be mục 3.2 #6 đòi Quality Gate dựa trên **RAG Triad**: Context Relevance, Faithfulness, Answer
Relevance, với chặn phát hành Faithfulness ≥ 0,95 và Citation Precision = 1,00. RS đã phủ cạnh đầu (recall
của `_rank`, đo được không cần model). ④ phủ hai cạnh còn lại + Citation Precision.

Vì sao ④ **buộc gọi model** còn RS thì không: RS đo **hàm xếp hạng** (thuần, tất định, fixture được input,
tính được output). ④ đo **câu trả lời model đẻ ra** — thứ chỉ tồn tại sau khi chạy pipeline chat thật, lại
không tất định, nên phải sinh **live**; và chấm Faithfulness/Answer‑Relevance là phán đoán entailment tự
nhiên, không có bản deterministic đáng tin → LLM‑judge. Đó là lý do ④ giống `gate-eval-harness` (có `--live`,
tốn tiền, ngoài `pytest`), không giống RS.

**Module ảnh hưởng:** M8 (Chatbot/Search) — thuần test/eval, không đụng code sản phẩm.
**API endpoints:** không thêm/sửa/xoá.
**Bảng DB:** không đụng, không migration. Fixture tự chứa như RS/gate.
**AI/LLM:** khi `--live`: (1) sinh câu trả lời qua pipeline chat thật; (2) LLM‑judge chấm. Offline: chấm lại
trên snapshot đã sinh. Judge output **ngắn, có biên** để tránh runaway.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Biến Faithfulness/Answer‑Relevance/Citation‑Precision từ chữ trong báo cáo thành **số chạy được**, có gate.
- Bắt hồi quy chất lượng trả lời **trước** merge (đặc biệt khi sửa prompt — vd sentinel của ③, hay nâng SDK).
- Tái dùng RS/gate, không dựng lại từ đầu.

**Non-Goals:**
- Không đo Context Relevance (RS lo); không sửa code sản phẩm; không dựng CI; không đưa vào `pytest` mặc định.

## Decisions

### D1 — Chấm kết hợp (a)+(b), không đồng nhất một cách

| Metric | Cách chấm | Model? | Ngưỡng |
|---|---|---|---|
| Faithfulness | **(a) LLM‑judge**: từng khẳng định có được context (tin đã cite) bảo chứng không | ✅ | **≥ 0,95** (hard) |
| Answer Relevance | **(a) LLM‑judge**: câu trả lời có giải quyết đúng câu hỏi | ✅ | baseline + dung sai |
| Citation Precision | **(b) structural**: mọi `[n]` trỏ insight thật trong index đã phục vụ, không bịa | ❌ | **= 1,00** (hard) |

Citation Precision đo được **không cần model** vì nó là quan hệ cấu trúc `marker → mapping → insight`, đúng
thứ `chat-citation-integrity` làm đúng bằng cấu trúc — ④ là lưới bắt nếu nó vỡ. Faithfulness/Answer‑Relevance
không có bản structural đáng tin (so chuỗi bỏ sót diễn giải khác chữ) → judge.

### D2 — `--live` sinh + chấm; offline chạy lại trên snapshot

`--live`: mỗi kịch bản chạy pipeline chat thật (sinh câu trả lời + citations) rồi judge → tốn tiền, đo đúng
pipeline hiện tại. Không `--live`: chấm lại trên **snapshot câu trả lời** đã lưu (để review/CI‑nhẹ không đốt
quota mỗi lần). **Snapshot không thay cho `--live`**: nó đo câu đông lạnh, chỉ `--live` mới bắt hồi quy
prompt/model — ghi rõ giới hạn này (như gate ghi giới hạn fixture).

*Đã cân nhắc:* chỉ offline (fixture câu trả lời cứng). Bỏ — mất đúng khả năng bắt hồi quy prompt/model, là lý
do tồn tại của bộ đo.

### D3 — LLM‑judge có sai số → giảm nhiễu và báo cáo trung thực

Judge cũng là model, không tất định. Giảm nhiễu: prompt judge **đóng khung** (chấm từng khẳng định, verdict
ngắn có biên — supported / not‑supported / partial), nhiệt độ thấp, chạy trên context đã cite tường minh.
Baseline đóng băng kèm **dung sai** (không so bằng), báo cáo **per‑kịch‑bản** để một loại câu vỡ không chìm
trong trung bình (bài học RS D7). Judge output ngắn nên rủi ro runaway thấp — nhưng vẫn giữ biên, không để
judge tự do dài (bài học `gemini-structured-output`).

### D4 — 50 kịch bản phủ cả ba mode, nhãn grounding gán tay

Mở rộng bộ câu RS lên ~50, mỗi kịch bản ghi: `mode` (A/B/expanded), câu hỏi, và **tập insight đáng lẽ được
cite** (gán tay, tái dùng `must_have` của RS khi trùng). Faithfulness/Citation chấm dựa trên tập này; Answer
Relevance chấm dựa trên câu hỏi. Phủ cả câu **mở rộng** của `chat-scope-routing` (out‑of‑scope → sentinel →
global) vì đó là đường mới dễ sai grounding nhất.

### D5 — Gate là lệnh + ngưỡng, chưa nối CI

Repo chưa có CI (RS đã ghi nhận). ④ cấp **một lệnh** cho verdict PASS/FAIL theo ngưỡng D1 + báo cáo
per‑kịch‑bản. Nối vào CI hoãn cùng open question của RS — quyết khi dựng CI, không chặn ④.

## Risks / Trade-offs

- **[`--live` tốn tiền/chậm]** → mặc định offline‑snapshot; `--live` chạy có chủ đích khi sửa prompt/model.
  Ước lượng: 50 kịch bản × (1 sinh + ~1 judge) lượt gọi — ghi chi phí thật vào docstring sau lần đo đầu.
- **[Judge sai số làm gate rung]** → dung sai + báo cáo per‑kịch‑bản + verdict đóng khung (D3); không chốt
  Faithsfulness tuyệt đối mà đo hồi quy so với chính nó, riêng ngưỡng hard 0,95/1,00 theo báo cáo.
- **[Snapshot lệch pipeline thật]** → D2 ghi rõ snapshot chỉ để chạy lại rẻ, `--live` mới là chuẩn.
- **[Trùng Citation Precision với CI change]** → không trùng việc: CI *làm đúng* bằng cấu trúc, ④ *đo* — ④
  chính là test bắt nếu cấu trúc đó bị phá về sau.

## Migration Plan

1. Soạn 50 kịch bản (mở rộng bộ RS) + nhãn grounding gán tay; script sinh fixture giữ lại.
2. Harness: chế độ `--live` (sinh câu trả lời qua pipeline thật + LLM‑judge) và offline (chấm snapshot);
   structural Citation Precision không gọi model.
3. Chốt baseline (`--live`) + ngưỡng gate hard (Faithfulness ≥ 0,95, Citation = 1,00).
4. Docs: `CLAUDE.md` — khi nào chạy lại (sửa `CHAT_SYSTEM_PROMPT`, prompt mode B/sentinel, đổi model/SDK).

Rollback: code test, không đụng sản phẩm — gỡ ra không ảnh hưởng gì.

## Open Questions

- **Dùng model nào làm judge** (cùng Gemini Flash hay model khác)? Bắt đầu bằng chính Flash cho rẻ; nếu judge
  và model trả lời cùng lỗi hệ thống thì cân nhắc judge khác — quyết sau lần đo đầu.
- **Nối CI**: hoãn theo RS.
- **Answer Relevance có nên có ngưỡng hard?** Báo cáo chỉ chốt số cho Faithfulness/Citation; v1 để baseline +
  dung sai, nâng thành hard khi có đủ số đo.
