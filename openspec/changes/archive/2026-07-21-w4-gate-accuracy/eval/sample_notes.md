# Ghi chú mẫu 54 doc — T10 gate eval

Sinh 2026-07-21 bằng `scripts/eval_gate.py` (throwaway) trên mẫu đóng băng `sample_ids.txt`.
Gate `temperature=0.0` → chạy lại tái lập. **0 lỗi parse gate** trên 54 doc.

## Phân bố theo source_type
| source_type | n |
|---|---|
| rss | 39 |
| huggingface | 4 |
| github_trending | 4 |
| web_index | 3 |
| hackernews | 2 |
| reddit | 2 |

## Verdict CŨ (old_status, prompt trước) vs MỚI (gate_pass_new)
| | n |
|---|---|
| low_signal(old-fail) | 36 |
| analyzed(old-pass) | 18 |
| — | — |
| new PASS | 37 |
| new FAIL | 17 |

## Lật old→new
- low_signal→PASS (ứng viên FN được sửa, cần xác nhận SIGNAL): **19**
- analyzed→FAIL (gate siết lại): **0**
- giữ nguyên: **35**

> Đây MỚI là verdict gate. Chưa có ground truth — chờ cột human_label trong gate_eval.csv.
> Chú ý: 0 doc analyzed→FAIL nghĩa là trụ ② (AI/DS) đủ rộng để arXiv vẫn pass — rủi ro widening
> đã nêu ở proposal; việc chấm tay sẽ cho biết các pass đó là SIGNAL thật hay FP mới.