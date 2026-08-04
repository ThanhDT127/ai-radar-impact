# Proposal: gate-benchmark-durability

**Phase áp dụng:** Phase 1 (củng cố M4 AI Analysis — không thêm tính năng người dùng).

## Why

`CLAUDE.md` tuyên bố benchmark 54 doc của `w4-gate-accuracy` là tấm bảo vệ **duy nhất** cho tiêu chí
gate: *"chạy lại khi sửa `GATE_PROMPT` (không có unit test cho tiêu chí gate)"*. Benchmark đó hiện
**không chạy được**, và sẽ **tự hết hạn** vào khoảng 17/01/2027:

1. **Công cụ đã mất vĩnh viễn.** `scripts/eval_gate.py` bị xoá ở task 5.1 và **chưa từng được commit** —
   `git log --all -- backend/app/scripts/eval_gate.py` trả về rỗng. Hướng dẫn khôi phục ở
   `eval/measurement.md:79` (*"lấy lại từ git history"*) là **sai sự thật**, và nó nằm đúng file mà
   người cần dùng sẽ mở ra đọc.
2. **Artifact không đủ để chạy offline.** `gate_eval.jsonl` chỉ lưu `content_preview` ~300 ký tự,
   trong khi `build_gate_prompt` đọc **2000 ký tự đầu**. Muốn đo lại phải có DB.
3. **Dữ liệu nguồn có hạn sử dụng.** `retention_months=6 × 30 ngày = 180 ngày`; `purge_expired` chạy
   3h sáng VN mỗi ngày và `tombstone_older_than()` xoá `normalized_content`. 54 doc ingest ~21/07/2026
   → rỗng ruột khoảng **17/01/2027**. Sau mốc đó benchmark chết kể cả khi viết lại script.
4. **Runbook chết vì chính hành động archive.** Lệnh đầu tiên trỏ `openspec/changes/w4-gate-accuracy/eval/`,
   nay đã là `openspec/changes/archive/2026-07-21-w4-gate-accuracy/eval/`.

Hệ quả vận hành: **không ai được sửa `GATE_PROMPT` một cách an toàn** cho tới khi có lại bộ đo. Gate là
điểm chặn quyết định tin nào lên UI — hồi quy ở đây vô hình (gate loại → `low_signal` → không bao giờ
xuất hiện để ai đó phát hiện), đúng dạng lỗi mà `w4-gate-accuracy` đã đo được là **16/34 FN**.

Nguyên nhân gốc là mâu thuẫn giữa task 4.3 (*giữ benchmark chống hồi quy*) và 5.1 (*xoá script
throwaway*): giữ đạn, vứt súng. Nguyên tắc "dọn scaffolding" đúng cho code **dùng một lần**;
`eval_gate.py` được chính change đó tuyên bố là dùng lại mỗi khi sửa prompt — nó không phải throwaway,
nó chỉ nằm sai chỗ.

## What Changes

- **Harness đo gate sống ở `backend/tests/eval/`** (không phải `app/scripts/`) — nó là bộ đo, không
  phải công cụ vận hành. Đặt đúng chỗ làm mâu thuẫn 4.3-vs-5.1 tự tan thay vì tái diễn.
- **Benchmark tự chứa, độc lập DB**: fixture lưu **2000 ký tự** content đúng bằng cửa sổ gate đọc,
  cùng nhãn tay. Chạy lại không cần `raw_documents` còn sống → miễn nhiễm với tombstone-purge.
- **Snapshot 54 doc hiện có ngay lập tức** (trước hạn purge) từ DB đang chạy.
- **Sửa runbook**: đường dẫn sau archive + gỡ câu hướng dẫn khôi phục sai sự thật.
- **Chế độ offline mặc định** (so nhãn với verdict đã lưu, không gọi Vertex) và chế độ `--live` gọi
  Gemini thật để đo lại confusion matrix.

## Capabilities

### New Capabilities
- `gate-eval-harness`: bộ đo độ chính xác tiêu chí gate — fixture tự chứa, chạy lại được, sinh
  confusion matrix đối chiếu nhãn tay.

### Modified Capabilities
_(không có — tiêu chí gate giữ nguyên; đây là change về khả năng ĐO, không phải về điều được đo.)_

## Non-goals

- **Không** tune `GATE_PROMPT`. Quyết định 21/07 (*"chốt tại 94%, KHÔNG tune thêm"*) giữ nguyên; FP
  KrebsOnSecurity (tin hình sự lọt qua "duyệt mạnh trụ ④") vẫn để dành. Change này chỉ **khôi phục
  khả năng đo** để quyết định đó có thể được xem lại sau bằng số liệu.
- **Không** biến benchmark thành unit test chặn CI — 54 lần gọi Gemini/lần chạy là quá đắt cho mỗi
  commit; đây là bộ đo chạy tay khi sửa prompt.
- **Không** mở rộng mẫu ngoài 54 doc, không gán nhãn mới.
- **Không** đụng `retention_months` hay `purge_expired`.

## Dependencies

- `w4-gate-accuracy` (đã archive 21/07) — nguồn của 54 doc_id, nhãn tay, rubric và `measurement.md`.
- **Gấp về thời gian**: bước snapshot phải chạy **trước ~17/01/2027**, khi 54 doc còn `normalized_content`.

## Impact

- **Mới**: `backend/tests/eval/` (harness + fixture tự chứa + README cách chạy).
- **Sửa**: `openspec/changes/archive/2026-07-21-w4-gate-accuracy/eval/measurement.md` (runbook sai);
  `CLAUDE.md` mục gotcha gate (trỏ tới harness mới).
- **Không đụng**: `app/ai/prompts.py`, `analyzer.py`, schema DB, pipeline chạy thật.
