# Tasks: w4-gate-accuracy (T10)

> Số nền để đối chiếu (measurement `gemini-structured-output`, mẫu sạch 48 doc, 20/07): arXiv 100% pass,
> dev.to loại 83%, VnExpress 0%. Gate `temperature=0.0` → chạy lại tái lập chuẩn. Mục tiêu con số sau
> change KHÔNG phải "% pass giảm" mà là "trong nhóm bị loại mới, tỉ lệ đồng ý đáng loại" (xem design D2/rủi ro).

## 1. Viết lại tiêu chí gate (prompt)

- [x] 1.1 Viết lại `BỐI CẢNH CÔNG TY` trong `GATE_PROMPT` theo **4 trụ cột** (IoT/R&D · Agent-AI-DS · Smart Home · Bảo mật). AI/Agent/DS/ML tooling KHÔNG còn NOISE mặc định; giữ nguyên list NOISE (tiền ảo/game/Web3/điện thoại-tai nghe). **DoD:** đọc prompt thấy rõ 4 trụ cột; một tin về LLM agent không còn rơi vào "noise mặc định".
- [x] 1.2 **Xoá** `NGOẠI LỆ HỌC THUẬT` dạng thể loại; thay bằng **relevance theo trụ cột** + hàng rào chuyển-giao-vs-incrementalism (design D2). **Bỏ cờ override** ở thang điểm 0.2–0.4. **DoD:** không còn câu "bất kể có nhắc IoT hay không"; không còn dòng "flip pass/fail"; dải 0.2–0.4 chỉ còn MỘT nghĩa.
- [x] 1.3 Bảo mật hệ thống/dữ liệu → **duyệt mạnh** (design D3): hạ burden of proof cho tin bảo mật chạm trụ ④. **DoD:** một cảnh báo bảo mật có action rõ (không cần CVE ID cứng) vẫn pass.
- [x] 1.4 Ép `gate_reason` **khai trụ cột / lý do** (design D4), trong giới hạn ≤100 ký tự. **DoD:** reason mẫu nêu được "Trụ ②/④…" hoặc "Off-pillar…".
- [x] 1.5 Thêm **1 few-shot arXiv off-pillar → FAIL** (design D5); giữ 2 few-shot cũ. **DoD:** prompt có ví dụ paper học thuật bị loại vì không chạm trụ cột.
- [x] 1.6 Đồng bộ khối bối cảnh trong `ANALYSIS_PROMPT` để deep-analysis không lệch pha gate (nêu phòng AI/DS + bảo mật). **DoD:** hai prompt cùng một định nghĩa phạm vi công ty; phần còn lại của `ANALYSIS_PROMPT` giữ nguyên.

## 2. Harness đo (throwaway — Đường A, KHÔNG đụng DB)

- [x] 2.1 `scripts/eval_gate.py`: nhận danh sách doc_id (hoặc query mẫu), chạy qua `gate_analyze`, dump JSONL `{doc_id, source, title, verdict, actionability_score, content_type, gate_reason}`. **DoD:** chạy được, ra file JSONL đọc tay được. (Script này bị xoá ở 5.1.)
- [x] 2.2 Chọn **mẫu ~50 doc stratified** (design D7): rải theo nguồn (arXiv/dev.to/HN/Reddit/VN) **và** theo verdict, **over-sample nhóm `low_signal`** để săn FN. Đóng băng danh sách doc_id vào change. **DoD:** danh sách 50 doc_id lưu trong folder change; ghi rõ phân bổ nguồn × verdict.
- [x] 2.3 Viết **rubric SIGNAL/NOISE** ra giấy TRƯỚC khi chấm (chống trôi giữa các lần chấm), rồi gán nhãn tay 50 doc → JSONL có cột `human_label` + `human_reason`. **DoD:** rubric + 50 nhãn lưu trong change.

## 3. Đo trước/sau

- [x] 3.1 Chạy **prompt CŨ** (trước 1.x) trên 50 doc đóng băng → `matrix_before` (TP/FP/FN/TN). **DoD:** confusion matrix baseline lưu trong `measurement.md`.
- [x] 3.2 Chạy **prompt MỚI** trên đúng 50 doc đó → `matrix_after`. **DoD:** matrix sau + delta so baseline.
- [x] 3.3 **Bảng accuracy theo nguồn** trước/sau (đặc biệt arXiv, dev.to). **DoD:** bảng dùng được cho quyết định giữ/cắt nguồn, thay bảng đo 20/07.
- [x] 3.4 Đọc riêng đống **FP và FN** (nhất là arXiv chuyển pass→fail): phân loại pattern lỗi; ghi ca FN nào do bằng chứng nằm sau ký tự 2000 (design/rủi ro truncation). **DoD:** danh sách pattern lỗi + kết luận truncation có phải nguyên nhân chính không.

## 4. Lặp & chốt

- [x] 4.1 Tinh chỉnh prompt cho pattern lỗi ở 3.4 (đặc biệt biên độ trụ ② để không tái tạo FN cũ); chạy lại 50 doc (temp=0.0 tái lập). **DoD:** trong nhóm bị loại mới, tỉ lệ người chấm đồng ý "đáng loại" đạt mức chấp nhận (chốt ngưỡng khi chấm).
- [x] 4.2 Bảng **accuracy cuối cùng trước/sau** trong `measurement.md`; ghi giới hạn (n<5 chỉ là tín hiệu). **DoD:** khớp DoD của T10 — "có bảng đánh giá độ chính xác gate".
- [x] 4.3 Lưu bộ **50 doc + nhãn** làm mini-benchmark chống hồi quy (kèm ghi chú: chạy lại khi sửa prompt gate về sau). **DoD:** benchmark + hướng dẫn dùng lại nằm trong change.

## 5. Dọn dẹp

- [x] 5.1 **Xoá `scripts/eval_gate.py`** sau khi có số (giữ prod sạch); giữ lại JSONL benchmark + `measurement.md` trong folder change. **DoD:** không còn script throwaway trong `backend/app/scripts/`; bằng chứng đo vẫn còn.
- [x] 5.2 Cập nhật `CLAUDE.md` mục taxonomy/gotcha nếu tiêu chí gate đổi hành vi đáng kể (vd: bảo mật duyệt mạnh, arXiv nay lọc theo relevance). **DoD:** người đọc sau hiểu gate hiện phán theo 4 trụ cột.
