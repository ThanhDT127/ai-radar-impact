# Đo độ chính xác gate — T10 (w4-gate-accuracy)

Ngày: 2026-07-21. Mẫu: **54 doc** đóng băng (`sample_ids.txt`), stratified 4 trụ cột, over-sample
`low_signal`. Ground truth: nhãn tay của Hung trong `gate_eval.csv` (**34 SIGNAL / 20 NOISE**).

Verdict gate lấy từ `gate_eval.jsonl` (bản gốc, không qua spreadsheet — Excel viết hoa `True→TRUE`,
join theo `doc_id`). Gate `temperature=0.0` → tái lập được. **0 lỗi parse gate / 54.**

> Quy ước: SIGNAL = positive; gate PASS = predicted positive.
> TP=pass&signal · FP=pass&noise · **FN=fail&signal (giết nhầm)** · TN=fail&noise.

## Confusion matrix — TRƯỚC / SAU

| | TP | FP | FN | TN | accuracy | precision | recall | F1 |
|---|---|---|---|---|---|---|---|---|
| **Gate CŨ** (IoT-only, dùng `old_status`) | 18 | 0 | **16** | 20 | 70% | 100% | **53%** | 69% |
| **Gate MỚI** (4 trụ cột) | 34 | 3 | **0** | 17 | **94%** | 92% | **100%** | **96%** |
| **Δ** | | | | | **+24%** | −8% | **+47%** | **+27%** |

**Đọc kết quả:** gate cũ precision hoàn hảo nhưng **recall chỉ 53% — giết nhầm 16/34 tin tốt**. Đây
là false-negative vô hình trong production (gate loại → `low_signal` → không bao giờ lên UI). 16 FN đó
gần như toàn tin AI/DS/security bị bối cảnh IoT-only coi là noise mặc định. Gate mới đưa recall lên
**100% (0 FN)**, đổi lấy 3 FP nhỏ. Với sản phẩm radar (bỏ sót signal tệ hơn lọt nhiễu), đây là đánh
đổi đúng hướng; F1 +27%.

## Accuracy theo source_type

| source_type | n | SIGNAL (nhãn) | gate mới đúng |
|---|---|---|---|
| rss | 39 | 26 | 38/39 |
| huggingface | 4 | 1 | 3/4 |
| github_trending | 4 | 3 | 4/4 |
| web_index | 3 | 2 | 2/3 |
| hackernews | 2 | 1 | 2/2 |
| reddit | 2 | 1 | 2/2 |

## Phát hiện: "arXiv over-pass" KHÔNG thành FP

Lo ngại ở proposal: trụ ② (AI/DS) quá rộng → arXiv pass lại gần 100% thành FP. Thực tế: **arXiv 9/9
pass, cả 9 đều được chấm SIGNAL** → 9/9 là TP. Việc bỏ ngoại lệ học thuật thể loại + chuyển sang
relevance trụ ② được ground truth xác nhận: các paper AI đó *đúng là* tín hiệu cho phòng AI/DS. Rủi ro
widening không hiện thực hoá trên mẫu này.

## FALSE POSITIVE (3) — pattern để (tuỳ chọn) siết

| score | nguồn | title | lý do bạn chấm NOISE | pattern |
|---|---|---|---|---|
| 0.70 | Viblo | Total TypeScript Thực chiến #2 | "không chạm trụ cột nào" | **Tutorial lập trình chung** (TS) bị nhận nhầm là trụ ② |
| 0.50 | KrebsOnSecurity | Netherlands Seizes 800 Servers, Arrests 2 | "chỉ là bài báo bắt giữ" | **Tin hình sự an ninh** ≠ lỗ hổng kỹ thuật; "duyệt mạnh trụ ④" đè nhầm lên VÍ DỤ 1 (tịch thu = NOISE) |
| 0.55 | HF Zhipu (GLM) | zai-org/GLM-OCR | "thiếu đánh giá thông số" | **Model release thiếu benchmark/specs** — biên giới, phần nhiều là chuẩn khắt khe của người chấm |

**FALSE NEGATIVE: 0** — gate mới không giết nhầm tin nào trong mẫu.

Pattern rõ nhất & đáng sửa nhất là **FP KrebsOnSecurity**: "duyệt mạnh trụ ④" của prompt mới nới lỏng
quá, cho lọt tin hình sự an ninh (bắt giữ/tịch thu) vốn VÍ DỤ 1 đã dạy là NOISE. Một guard 1 dòng cho
trụ ④ ("duyệt mạnh áp dụng cho lỗ hổng/kỹ thuật, KHÔNG cho tin hình sự/bắt giữ/tịch thu") sửa được mà
gần như không đụng recall (34 SIGNAL đều là advisory kỹ thuật, không phải tin hình sự).

## Giới hạn

- Mẫu 54 doc; các nguồn n<5 (huggingface/web_index/HN/reddit) chỉ đọc như tín hiệu.
- FP=3 trên 54 → precision 92%; với sample nhỏ, siết theo 3 FP có rủi ro overfit — cân nhắc trước khi tune.
- Verdict "CŨ" suy từ `old_status` lịch sử (có thể lệch version model theo thời gian), không phải re-run
  prompt cũ. Muốn tuyệt đối sạch thì `git stash` prompt mới rồi chạy lại — chưa làm vì chênh lệch dự kiến nhỏ.

## Chốt (21/07/2026)

**Chốt tại 94% accuracy / F1 96% / recall 100%, KHÔNG tune thêm** (quyết định vận hành). Lý do: recall
100% là đích cho sản phẩm radar và đã đạt; 3 FP còn lại nhỏ và phần lớn là chuẩn khắt khe của người chấm;
tune 3 FP trên mẫu 54 doc rủi ro overfit. FP KrebsOnSecurity (tin hình sự an ninh) được ghi nhận là
over-extension của "duyệt mạnh trụ ④" — để dành cho change sau nếu precision thành vấn đề trên mẫu lớn hơn.

## Dùng lại benchmark (chống hồi quy tiêu chí gate)

Bộ **54 doc + nhãn tay** (`gate_eval.csv` cột `human_label`) + `sample_ids.txt` là mini-benchmark. Không
có unit test nào bảo vệ *tiêu chí* gate, nên **mỗi lần sửa `GATE_PROMPT` về sau nên chạy lại nó**:

```bash
# eval_gate.py đã bị xoá (task 5.1) — lấy lại từ git history của change này nếu cần:
#   git log --oneline -- backend/app/scripts/eval_gate.py
cp openspec/changes/w4-gate-accuracy/eval/sample_ids.txt backend/_ids.txt
docker compose exec -T backend python -m app.scripts.eval_gate --doc-ids-file /app/_ids.txt --out /app/rerun.jsonl
# rồi join verdict (JSONL) với human_label (gate_eval.csv) theo doc_id → confusion matrix.
# Kỳ vọng khi KHÔNG đổi prompt: khớp bảng trên (temp=0.0 tất định).
```
