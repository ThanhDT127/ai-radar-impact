## Why

Đây là **T10 (W4)** trong lịch trình: *"Đánh giá & tinh chỉnh độ chính xác phân loại — gate:
ảnh hưởng vs thông báo"*. Change này cũng hiện thực hoá cái tên `widen-gate-company-context` đã được
"đặt gạch" trong Non-Goals của `gemini-structured-output` (20/07).

Đo được từ `gemini-structured-output` (mẫu sạch 48 doc, sau migration 009):

| Nguồn | Qua gate | Ghi chú |
|---|---|---|
| arXiv (mọi category) | **20/20 = 100%** | gate gần như không lọc |
| dev.to (ML + AI) | 3/18 = 17% (loại **83%**) | gate mạnh tay |
| VnExpress Số hóa | 0/2 | |

Hai vấn đề gốc rễ đằng sau con số này:

**1. `BỐI CẢNH CÔNG TY` trong `GATE_PROMPT` mâu thuẫn với chính công ty.** Dòng hiện tại ghi *"Mọi tin
KHÔNG phục vụ hệ sinh thái này [chỉ liệt kê IoT/Smart Home] đều mặc định là NOISE"*. Nhưng phạm vi thật
của công ty gồm **4 trụ cột**: (①) IoT — phòng R&D, (②) **Agent / AI / Data Science — phòng AI/DS mới**,
(③) Smart Home, (④) **Bảo mật hệ thống/dữ liệu — duyệt mạnh**. Gate đang coi AI/Agent/DS tổng quát là
NOISE mặc định → phần lớn 83% dev.to bị loại nhiều khả năng là **false negative** (giết nhầm tin AI/ML
thật sự liên quan), không phải true negative.

**2. `NGOẠI LỆ HỌC THUẬT` là whitelist đội lốt rubric.** Nó hỏi *"đây có phải arXiv paper về thuật toán
AI không?"* — câu hỏi **thể loại**, mà mọi bài arXiv đều đúng → sập về "nếu là arXiv → pass". Nó không có
đường FAIL, cắt luôn dây neo bối cảnh công ty (*"bất kể có nhắc IoT hay không"*), và bị truncation 2000
ký tự khuếch đại (gate chỉ đọc abstract — vốn bài arXiv nào cũng đọc lên như "core research"). Kết quả:
gate không phân biệt gì trên nguồn chiếm ~40% mẫu; chất lượng arXiv phụ thuộc hoàn toàn vào việc chọn
category lúc seed.

Đồng thời, nửa "đánh giá độ chính xác" của T10 (chấm tay ~50 doc, bảng accuracy trước/sau) **chưa bắt
đầu**, và hiện **không đo được** vì kết quả gate (`gate_reason`/`evidence`/`score`) chỉ nằm trong log rồi
cuộn đi (design D3 của change trước cố ý chỉ thêm cột `gate_skipped`).

## What Changes

**A. Viết lại tiêu chí gate (đây là nơi DUY NHẤT được phép đổi tiêu chí — Non-Goal của change trước):**
- Viết lại `BỐI CẢNH CÔNG TY` theo **4 trụ cột**; AI/Agent/DS tổng quát KHÔNG còn là NOISE mặc định.
- Bảo mật hệ thống/dữ liệu → **duyệt mạnh** (ngưỡng thấp, ưu tiên pass).
- **Xoá** ngoại lệ học thuật dạng thể loại; thay bằng **relevance theo 4 trụ cột**: paper (kể cả arXiv)
  chạm ≥1 trụ cột → xét pass; không chạm trụ nào → fail, bất kể "có tính học thuật".
- Giữ **hàng rào chất lượng** đè lên relevance: chuyển-giao-được/nền-tảng thì pass, chỉ incrementalism
  leaderboard (SOTA +0.x%, biến thể attention thứ N) thì fail. *Relevance mở cửa, tính chuyển-giao soát vé.*
- **Dời quyết định vào điểm số, bỏ cờ override** → xoá mâu thuẫn "dải 0.2–0.4 vừa pass vừa fail".
- `gate_reason` phải **nêu trụ cột / lý do** đã dùng (auditable cho việc chấm tay).
- Thêm 1 few-shot **arXiv-off-pillar → FAIL** để dạy hành vi mới (few-shot cũ đều mùi security).
- Đồng bộ khối bối cảnh trong `ANALYSIS_PROMPT` để deep-analysis không lệch pha với gate.

**B. Đo độ chính xác (throwaway harness — Đường A, KHÔNG đụng DB):**
- Script `scripts/eval_gate.py` chạy mẫu đóng băng qua gate → JSONL `{doc_id, source, title, verdict, score, reason}`.
- Mẫu ~50 doc **stratified** theo nguồn **và** theo verdict — cố ý over-sample nhóm `low_signal` để săn
  false negative (FN vô hình trong production).
- Người gán nhãn SIGNAL/NOISE → **confusion matrix trước/sau** + bảng accuracy theo nguồn.
- Bộ 50 doc có nhãn giữ lại làm **mini-benchmark chống hồi quy** (không có test nào bảo vệ *tiêu chí* gate).
- Gate chạy `temperature=0.0` → chạy lại tái lập chuẩn, delta quy được cho prompt.

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `ai-analysis`: tiêu chí đánh giá của gate MUST theo phạm vi công ty 4 trụ cột; paper học thuật được
  xét theo **relevance** (chạm trụ cột) chứ không theo **thể loại**; bảo mật được duyệt mạnh; quyết định
  pass/fail nằm trong điểm số (không còn cờ override). Đây là lần đầu tiêu chí gate được spec hoá.

## Impact

- **Code**: `backend/app/ai/prompts.py` (`GATE_PROMPT`: bối cảnh + ngoại lệ + thang điểm + few-shot;
  `ANALYSIS_PROMPT`: đồng bộ bối cảnh). `backend/app/scripts/eval_gate.py` (throwaway — xoá ở task dọn dẹp).
- **DB**: **không** — schema đứng nguyên ở migration 009 (không đẻ migration 010). Món "lưu gate result"
  của design D3 vẫn để dành (Đường C, tách change riêng nếu về sau cần đo liên tục).
- **Chi phí**: vòng đo tốn ~50–100 gate-call (temp=0.0, output nhỏ → rẻ); chạy local, không production.
- **Rủi ro**: nới trụ ② (AI/Agent) RẤT rộng — arXiv có thể pass lại gần 100% nhưng *đổi lý do*. Hàng rào
  chất lượng (chuyển-giao vs incrementalism) + bảng accuracy theo nguồn là thứ giữ không cho loãng.

## Non-goals

- **Không** đẻ migration / không lưu `gate_score`/`gate_reason`/`evidence` xuống DB (đó là Đường C, đã
  cân nhắc và hoãn ở buổi explore 21/07).
- **Không** đổi `IMPACT_LABEL_MAP`, `_compute_urgency`, hay logic delivery.
- **Không** đổi truncation content (gate 2000 / deep 6000) — *theo dõi* trong eval; nếu FN do bằng chứng
  nằm sau ký tự 2000 là chính, mở follow-up riêng, không gộp vào 2 ngày này.
- **Không** bật `response_schema` cho deep-analysis (đã chốt BỎ ở `gemini-structured-output`).
- **Không** đổi kiến trúc 2-pass (gate → deep) hay ngưỡng `MIN_CONFIDENCE = 0.3`.
