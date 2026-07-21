## Context

`GATE_PROMPT` (`app/ai/prompts.py`) đóng vai một Tech Lead hoài nghi, gạt tin nhiễu **trước** khi doc
vào deep-analysis đắt tiền. Nó quyết định pass/fail dựa trên:

1. `BỐI CẢNH CÔNG TY` — hiện chỉ liệt kê IoT/Smart Home/Edge/Robotics; "không phục vụ hệ sinh thái này
   = NOISE mặc định".
2. Ba trường **evidence** (`code_or_api`, `cve_or_regulation`, `benchmark_data`) làm burden of proof.
3. Thang điểm 0.0–1.0 (≥0.7 practical, 0.4–0.7 strategic, 0.2–0.4 theoretical, <0.2 noise).
4. Ba ngoại lệ: **HỌC THUẬT** (arXiv paper → pass 0.2–0.4), **ĐỨT GÃY** (deprecate/cấm vận → force
   pass ≥0.7), và luật ANTI-GENERALIZATION.

Gate chạy `temperature=0.0` + `response_schema` (từ `gemini-structured-output`) → đầu ra tất định và
đúng cấu trúc. Nhưng *tiêu chí phán đoán* chưa từng được đo hay spec hoá. Đo 20/07 phơi ra: arXiv 100%
pass (ngoại lệ học thuật), dev.to loại 83% (bối cảnh IoT-only coi AI tổng quát là noise).

Phạm vi công ty thật (chốt ở buổi explore 21/07) gồm **4 trụ cột**:

```
① IoT                     → phòng R&D
② Agent / AI / Data Science → phòng AI/DS (MỚI)   ← chưa có trong gate hiện tại
③ Smart Home
④ Bảo mật hệ thống/dữ liệu  → DUYỆT MẠNH           ← nâng từ "bảo mật thiết bị đầu cuối"
```

## Goals / Non-Goals

**Goals:**
- Gate phán "impact vs thông báo/hàn lâm" theo đúng phạm vi 4 trụ cột của công ty.
- Paper học thuật được xét theo **relevance** (chạm trụ cột), không theo **thể loại** (là arXiv).
- Có confusion matrix + bảng accuracy theo nguồn **trước/sau**, đo được, tái lập được.
- Để lại **mini-benchmark 50 doc có nhãn** làm lưới chống hồi quy tiêu chí gate.

**Non-Goals:**
- Không đẻ migration, không lưu kết quả gate xuống DB (Đường C — hoãn).
- Không đổi truncation, `MIN_CONFIDENCE`, `IMPACT_LABEL_MAP`, delivery, kiến trúc 2-pass.
- Không đổi ngoại lệ ĐỨT GÃY (đang đúng việc) — chỉ đụng ngoại lệ HỌC THUẬT + bối cảnh.

## Decisions

**D1 — Viết lại `BỐI CẢNH CÔNG TY` theo 4 trụ cột; AI/Agent/DS KHÔNG còn là NOISE mặc định.**
Đây là gốc rễ của 83% dev.to bị loại. Danh sách NOISE mặc định (tiền ảo, game, Web3, điện thoại/tai nghe
tiêu dùng) **giữ nguyên**, nhưng bổ sung rõ: nội dung Agent/LLM/AI/Data Science/ML tooling nay thuộc trụ
② → được xét bình thường, không mặc định noise.

**D2 — Thay ngoại lệ học thuật (thể loại) bằng relevance theo trụ cột, và bỏ cờ override.**
Logic mới:
```
Bài (kể cả arXiv) chạm ≥1 trụ cột?
  ├─ CÓ + là bảo mật hệ thống/dữ liệu ─────► duyệt mạnh (pass, điểm cao)  [D3]
  ├─ CÓ + chuyển-giao-được / đổi năng-lực-lõi ─► pass theo thang thường
  ├─ CÓ + chỉ incrementalism leaderboard ──► fail (hàng rào chất lượng)
  └─ KHÔNG chạm trụ nào ────────────────────► fail, bất kể "tính học thuật"
```
Vì paper chuyển-giao-được **tự earn ≥0.4 trên thang thường**, và paper lý-thuyết-thuần **ở lại <0.4**,
nên **không còn cần cờ "flip pass/fail"** — mâu thuẫn "dải 0.2–0.4 hai nghĩa" biến mất cùng lúc.
*Đánh đổi phải nói thẳng:* việc này **định nghĩa lại điểm số đo gì cho paper** — từ "có triển khai được
ngay" (nghĩa cũ, gây FN) sang "có liên quan năng lực + chuyển-giao được". Đây là thay đổi ngữ nghĩa có
chủ đích, không phải sửa lặt vặt.

**D3 — Bảo mật = duyệt mạnh, cơ chế như một ngoại lệ relevance nhẹ.**
Tin bảo mật hệ thống/dữ liệu (CVE, lỗ hổng stack, tấn công chuỗi cung ứng, rò rỉ dữ liệu, hardening)
chạm trụ ④ → hạ burden of proof, ưu tiên pass. Không cần CVE ID cứng mới qua; một cảnh báo bảo mật có
action rõ cho Security/Dev là đủ.

**D4 — `gate_reason` phải khai trụ cột / lý do đã dùng.**
Trong giới hạn ≤100 ký tự sẵn có, ép reason có cấu trúc: nêu **trụ cột nào** (hoặc "off-pillar") và
**lý do pass/fail** (vd: *"Trụ ②: model nhỏ chạy edge, chuyển-giao được"* / *"Off-pillar: lý thuyết tối
ưu thuần, không chuyển-giao"*). Đây là thứ biến ngoại lệ mờ thành ngoại lệ **kiểm toán được** khi chấm tay
— không cần thêm cột DB nào.

**D5 — Thêm 1 few-shot "arXiv off-pillar → FAIL", giữ 2 few-shot cũ.**
Hai few-shot hiện tại (deepfake NOISE, CVE xz-utils SIGNAL) đều mùi security → model neo "SIGNAL = giống
lỗ hổng". Thêm một ví dụ **paper học thuật bị loại vì không chạm trụ cột** để dạy hành vi mới của D2. Chỉ
thêm 1 (không thêm nhiều) để tránh phình token + overfit; đo lại sau khi thêm.

**D6 — Đo bằng throwaway harness, không đụng DB (Đường A).**
`temperature=0.0` nên một script chạy lại mẫu đóng băng là đủ cho before/after — không cần persist. Script
`scripts/eval_gate.py` dump JSONL; xoá ở task dọn dẹp sau khi có số (theo nguyên tắc giữ prod sạch). Bộ
JSONL có nhãn + `measurement.md` ở lại trong folder change làm bằng chứng + benchmark.

**D7 — Chiến lược lấy mẫu: stratified, cố ý over-sample `low_signal`.**
FP tự lộ trên dashboard; **FN vô hình** (gate loại → `low_signal` → không bao giờ lên UI). Nên mẫu ~50
phải: (a) rải theo nguồn (arXiv/dev.to/HN/Reddit/VN) vì pass-rate lệch nhau kinh khủng; (b) rải theo
verdict, lấy **đậm nhóm `low_signal`** để moi FN — đó là nơi các vết nứt của gate đang chôn tin tốt.

## Risks / Trade-offs

- **[Nới trụ ② quá rộng ⇒ arXiv pass lại gần 100%]** → hàng rào chất lượng D2 (chuyển-giao vs
  incrementalism) + bảng accuracy theo nguồn. Con số cần theo dõi KHÔNG phải "% pass giảm bao nhiêu" mà là
  *"trong nhóm bị loại mới, tỉ lệ người chấm đồng ý đáng loại"*.
- **[Đánh văng ngược về FN cũ khi siết off-pillar]** → chạy lại 20 doc arXiv qua gate mới, ĐỌC TAY nhóm
  chuyển pass→fail: chúng thật vô giá trị hay ta vừa tái tạo FN? Chỉnh biên độ trụ cột tới khi cân.
- **[Single annotator ⇒ ground truth chủ quan]** → viết rubric SIGNAL/NOISE ra giấy **trước** khi chấm,
  để lần chấm sau (và sau tune) nhất quán với chính nó.
- **[Truncation 2000 khuếch đại lỗi]** → không sửa trong change này; nhưng eval phải **ghi nhận** ca FN
  nào do bằng chứng nằm sau ký tự 2000. Nếu đó là nguyên nhân chính → mở follow-up nâng ngưỡng.
- **[Không có test cho tiêu chí gate]** → mini-benchmark 50 doc có nhãn (D6) là lưới an toàn; bất kỳ chỉnh
  prompt gate nào về sau nên chạy lại nó.

## Migration Plan

Không có thay đổi schema. Rollback = revert commit prompt (+ xoá script nếu chưa xoá). Vì gate `temp=0.0`,
revert prompt là khôi phục hành vi cũ y nguyên.

## Open Questions

- Bối cảnh trong `ANALYSIS_PROMPT` (deep-analysis) nên đồng bộ tới đâu? Nó đã có luật "KHÔNG ÉP BUỘC LIÊN
  QUAN" cho foundation model, nhưng chưa nêu phòng AI/DS và bảo mật như trụ cột. Đề xuất: đồng bộ tối thiểu
  khối bối cảnh, giữ nguyên phần còn lại (task 1.6).
- Ngưỡng "duyệt mạnh" của bảo mật (D3) có cần con số cụ thể, hay để định tính? Đề xuất định tính trước, đo
  rồi mới siết bằng số nếu thấy over-fire.
- Bao nhiêu doc là "đủ" cho mẫu? DoD gốc của T10 nói ~50; measurement trước chốt sớm ở 48. Giữ ~50, ghi rõ
  nguồn n<5 chỉ đọc như tín hiệu.
