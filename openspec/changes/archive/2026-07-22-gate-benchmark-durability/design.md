## Context

`w4-gate-accuracy` (archive 21/07/2026) đo tiêu chí gate trên 54 doc gán nhãn tay và chốt ở accuracy
94% / recall 100% / precision 92%. Bằng chứng đo còn nguyên trong `eval/`, nhưng **khả năng đo lại đã
mất**:

| Thành phần | Trạng thái |
|---|---|
| 54 nhãn tay (`gate_eval.csv`) | ✅ còn |
| `sample_ids.txt`, rubric, `measurement.md` | ✅ còn |
| `scripts/eval_gate.py` (công cụ chạy) | ❌ xoá ở task 5.1, **chưa từng commit** |
| Nội dung doc để nạp vào gate | ⚠️ chỉ có `content_preview` ~300 ký tự trong JSONL; bản đủ nằm trong DB và **hết hạn ~17/01/2027** |

Xác minh: `git log --all -- backend/app/scripts/eval_gate.py` → rỗng. Hướng dẫn khôi phục ở
`measurement.md:79` (*"lấy lại từ git history"*) không thực hiện được.

Ràng buộc quan trọng: `gate_analyze(title, content)` nhận **title + content trực tiếp**, không đọc DB;
`build_gate_prompt` cắt `content[:2000]`. Nghĩa là một fixture chứa `title` + 2000 ký tự đầu là **đủ và
đúng** để tái lập gate — không cần `raw_documents` còn sống.

**Module ảnh hưởng:** M4 (AI Analysis) — chỉ phần đo, không đụng pipeline chạy thật.
**API endpoints:** không thêm, không sửa.
**Bảng DB:** chỉ **đọc** `raw_documents` một lần ở bước snapshot; không migration, không ghi.
**AI/LLM:** Gemini 2.5 Flash qua Vertex AI, `temperature=0.0` (tất định, tái lập được), prompt
`GATE_PROMPT` hiện hành. Grounding không áp dụng — gate là bài toán phân loại nhị phân, không sinh nội dung.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Sửa `GATE_PROMPT` trở lại thành việc **an toàn**: có bộ đo chạy được trước/sau.
- Benchmark sống độc lập DB → miễn nhiễm với `purge_expired`.
- Người sau đọc runbook và chạy được **mà không cần hỏi ai**.

**Non-Goals:**
- Không tune `GATE_PROMPT` (quyết định 21/07 giữ nguyên).
- Không chạy trong CI — 54 lần gọi Gemini mỗi commit là quá đắt.
- Không mở rộng mẫu, không gán nhãn mới.

## Decisions

### D1 — Harness ở `backend/tests/eval/`, không phải `app/scripts/`

Đây là quyết định trung tâm, vì nó xử lý **nguyên nhân gốc** chứ không chỉ triệu chứng.

Mâu thuẫn cũ: task 4.3 muốn giữ benchmark chống hồi quy, task 5.1 muốn xoá script throwaway khỏi
`app/scripts/`. Cả hai đều đúng theo cách hiểu của mình, và kết quả là *giữ đạn, vứt súng*.

Mâu thuẫn tan khi đặt đúng chỗ: `app/scripts/` là **công cụ vận hành** (chạy trên production, đụng dữ
liệu thật) — một bộ đo không thuộc về đó, nên phản xạ "dọn cho sạch prod" là đúng. Nhưng `backend/tests/`
là nơi **code đo lường thuộc về**, và không ai có phản xạ xoá test. Đặt ở đó thì lần sau không cần ai
phải nhớ ngoại lệ.

*Đã cân nhắc:* (a) giữ ở `app/scripts/` + comment "đừng xoá" — dựa vào trí nhớ người đọc, đúng thứ vừa
thất bại; (b) để trong thư mục change — change bị archive thì code chết theo, và archive là chính hành
động vừa làm hỏng runbook.

### D2 — Fixture tự chứa 2000 ký tự, không phải doc_id + DB

Lưu `{doc_id, source, source_type, title, content_2000, human_label, human_reason}` vào JSONL trong repo.
2000 ký tự **đúng bằng** cửa sổ `build_gate_prompt` đọc, nên fixture không phải xấp xỉ — nó *là* đầu vào
thật của gate. Doc bị purge sau này cũng không ảnh hưởng.

Chi phí: 54 × 2000 ký tự ≈ 108 KB text trong repo. Chấp nhận được cho thứ duy nhất bảo vệ gate.

*Đã cân nhắc:* giữ `sample_ids.txt` + đọc DB lúc chạy — chính là thiết kế hiện tại, và là lý do
benchmark có hạn sử dụng.

### D3 — Hai chế độ: offline mặc định, `--live` để đo thật

- **Offline** (mặc định, 0 đồng, chạy trong vài giây): so `human_label` với verdict đã lưu lần trước,
  in confusion matrix. Dùng để kiểm tra fixture nguyên vẹn và để đọc lại kết quả cũ.
- **`--live`**: gọi Vertex thật trên 54 fixture, sinh matrix mới, **diff với matrix baseline** đã lưu.
  Đây là chế độ chạy khi sửa `GATE_PROMPT`.

Tách vậy để "chạy thử harness" không tốn tiền, còn "đo lại thật" là hành động có chủ đích.

### D4 — Không chặn CI, nhưng đặt cạnh test để không bị quên

`pytest` mặc định **không** chạy phần `--live` (đánh dấu skip trừ khi có cờ). Phần offline có thể chạy
tự do — nó bắt được lỗi "fixture hỏng/thiếu cột", tức là bảo vệ chính benchmark.

### D5 — Giữ nguyên 54 nhãn tay

Nhãn là ground truth do người chấm theo rubric viết trước. Gán lại sẽ mất khả năng so với `matrix_before`
/`matrix_after` của `w4-gate-accuracy`. Copy nguyên văn, không diễn giải lại.

## Risks / Trade-offs

- **[Bước snapshot phải chạy trước ~17/01/2027]** → Đặt là task đầu tiên, trước cả việc viết harness.
  Nếu doc đã bị purge, còn `content_preview` 300 ký tự trong JSONL cũ — đủ để giữ mẫu nhưng **không**
  tái lập được số cũ; phải ghi rõ trong `measurement.md` là mẫu đã suy giảm.
- **[Fixture đóng băng ≠ prompt đóng băng]** → Nếu sau này `build_gate_prompt` đổi cửa sổ khỏi 2000 ký
  tự, fixture thành sai lệch âm thầm. Mitigation: harness assert `2000` khớp hằng số thật trong code,
  fail rõ ràng nếu lệch.
- **[Mẫu 54 doc là ảnh chụp tháng 7/2026]** → Nguồn và phong cách tin đổi theo thời gian; benchmark đo
  *hồi quy so với chính nó*, không đo chất lượng tuyệt đối trên tin mới. Ghi rõ giới hạn này trong README.
- **[`--live` tốn tiền và quota]** → 54 lần gọi/lần chạy, ăn chung `MAX_DAILY_ANALYSIS`. Ghi chi phí ước
  tính trong README để người chạy biết trước.

## Migration Plan

1. Snapshot 54 doc từ DB đang chạy → fixture JSONL (**làm trước tiên**, đây là bước có hạn).
2. Viết harness đọc fixture; xác minh chế độ offline tái lập đúng matrix trong `measurement.md`.
3. Chạy `--live` một lần trên `GATE_PROMPT` hiện hành → xác nhận khớp bảng 21/07 (temp=0.0 tất định).
   Lệch thì điều tra trước khi chốt — có thể là drift version model.
4. Sửa runbook trong archive + `CLAUDE.md`.

Rollback: change này chỉ thêm file test và sửa docs — gỡ bằng cách xoá thư mục, không ảnh hưởng runtime.

## Quyết định đã chốt (22/07/2026)

- **Baseline khi đo lại không khớp bảng 21/07** (nghi model version drift): **ghi cả hai số**, lấy số
  đo lại làm mốc so sánh về sau, và ghi rõ nguyên nhân lệch trong `measurement.md`. Không im lặng chọn
  một trong hai — bảng 21/07 vẫn là dữ kiện lịch sử có giá trị, còn thứ dùng để phát hiện hồi quy phải
  là số đo trên chính môi trường hiện tại.
- **Không** đưa guard FP tin hình sự (trụ ④) vào change này. Giữ change thuần về **khả năng đo**; guard
  đó thành change riêng, và nhờ có harness thì nó sẽ có số liệu trước/sau đàng hoàng thay vì sửa mù.
