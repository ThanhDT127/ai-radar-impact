# Tasks: chat-scope-routing

**Phase:** 2 (M8 Chatbot). Backend + Frontend + Test. Không migration, không n8n.

> Phụ thuộc cứng: **`chat-context-isolation` (①) land trước** — badge scope xây trên mô hình cô lập luồng
> của ①. Thứ tự trong change: backend sentinel/fallback → frontend badge → xác minh thủ công → docs.

## 1. Sentinel out‑of‑scope trong prompt mode B (Backend/AI)

- [x] 1.1 Thêm luật sentinel vào prompt mode B (`build_chat_insight_prompt`/`CHAT_SYSTEM_PROMPT`): nếu câu hỏi **không thể** trả lời từ nội dung bài này, in đúng một dòng `[[NGOÀI_PHẠM_VI_BÀI]]` và không gì khác; còn trả lời được **dù chỉ một phần** thì **không** in sentinel (design D3, phát dè dặt). **DoD:** đọc prompt thấy rõ điều kiện phát và điều kiện KHÔNG phát; không dùng `response_schema`.
- [x] 1.2 Xác nhận sentinel là token văn bản thuần, không trùng nội dung tự nhiên, server tra được như marker `[n]`. **DoD:** hằng số sentinel định nghĩa một chỗ, dùng chung backend.

## 2. Auto‑fallback trong service (Backend)

- [x] 2.1 `_answer_insight`: sau lượt gọi B, nếu kết quả là sentinel → **không** trả về sentinel cho người dùng; thay vào đó dựng context mở rộng = **insight block của bài B + index toàn cục** (tái dùng đường `_answer_global`: lọc published+is_primary+window → `_rank` → top‑K → index nén) và gọi model lần 2 (design D4). **DoD:** câu ngoài phạm vi bài → 2 lượt gọi, trả lời dựa trên dữ liệu global thật, không phải sentinel.
- [x] 2.2 Câu trả lời mở rộng: `mode="expanded"`, citation lấy từ mapping `[n]` của lượt 2, và nêu rõ đã tìm toàn hệ thống. **DoD:** response mang `mode="expanded"` + citations từ global; answer có câu dẫn "bài này không nhắc… tìm toàn hệ thống…".
- [x] 2.3 Trần 2 lượt: câu mở rộng dùng đúng 2 (`MAX_MODEL_CALLS_PER_QUESTION`), lượt 3 raise; `chat_logs` ghi `model_calls=2` (design D5). **DoD:** test khẳng định tổng lượt gọi = 2 cho câu mở rộng, = 1 cho câu in‑scope.
- [x] 2.4 Mở rộng nhưng global cũng không có tin → fail‑closed "không tìm thấy trong toàn hệ thống" (giữ nguyên cơ chế grounding). **DoD:** ca không có tin nào khớp → câu trả lời trung thực, `citations` rỗng.
- [x] 2.5 Cập nhật comment `mode` trong `schemas/chat.py`: `"insight" | "global" | "meta" | "expanded"`. **DoD:** comment khớp giá trị thật.

## 3. Badge phạm vi hai chiều (Frontend)

> Phụ thuộc ①: chuyển scope = đổi `scopeKey` = đổi luồng.

- [x] 3.1 Trên trang chi tiết, thay/nâng context chip thành **badge chỉ báo scope**: hiện "Phạm vi: Bài đang xem" hoặc "Phạm vi: Toàn hệ thống", kèm 1‑click chuyển **hai chiều** (design D7). **DoD:** đang ở bài bấm 1 lần sang toàn hệ thống; bấm lần nữa quay lại bài — không điều hướng.
- [x] 3.2 Chuyển scope bằng badge đổi luồng hội thoại tương ứng (cô lập của ①). **DoD:** toggle sang toàn hệ thống hiện luồng toàn cục; quay lại bài hiện luồng bài.
- [x] 3.3 Đánh dấu câu trả lời `mode="expanded"` cho người dùng biết nó tìm toàn hệ thống, không chỉ bài đang xem. **DoD:** bong bóng trả lời mở rộng có nhãn/chỉ báo phân biệt với trả lời trong phạm vi bài.
- [x] 3.4 `api/chat.ts`: đọc `mode` (thêm `"expanded"` vào type). **DoD:** type khớp giá trị backend trả.

## 4. Xác minh thủ công (Test)

> Chat prompt **chưa có eval harness** (chỉ gate có) — phần này chạy tay có chủ đích, ghi kết quả.
>
> **KẾT QUẢ ĐO 25/07/2026** (bài thử: `OWASP/Nettacker` `57b46c99`, model thật, đọc từ `chat_logs`):
>
> | Bộ | Số câu | mode | Tổng lượt gọi | Độ trễ (min/tb/max) |
> |---|---|---|---|---|
> | in‑scope | 6 | `insight` ×6 | 6 (đúng 1/câu) | 2,1 / 4,1 / 5,7 s |
> | out‑of‑scope | 5 | `expanded` ×5 | 10 (đúng 2/câu) | 6,9 / 13,0 / 18,7 s |
>
> - **Sentinel giả: 0/6 (0%)** trên bộ in‑scope — prompt KHÔNG quá nhạy, không cần chỉnh lại task 1.1.
> - **Bắt đúng: 5/5** trên bộ out‑of‑scope.
> - Citation của câu mở rộng trỏ **tin khác có thật**, không bịa từ bài đang mở: hỏi observability →
>   `SigNoz/signoz` (`ae26a0e7`); hỏi text‑to‑SQL/BI → `Canner/WrenAI` (`eae97120`). Không câu nào trích
>   ngược về `57b46c99`.
> - Câu mở đầu đúng như thiết kế: *"Bài bạn đang xem không nhắc tới điều này; tìm trên toàn hệ thống thì thấy:"*
> - **0 câu để lọt sentinel ra ngoài.**
> - Độ trễ mở rộng ≈ **3,2×** câu in‑scope — đúng cái mà ⑤ streaming sẽ che (Risk đã khai trong design).

- [x] 4.1 Bộ câu **in‑scope** hỏi khi đang mở một bài (đáp án nằm trong bài): khẳng định **không** bắn sentinel, 1 lượt gọi, `mode="insight"`. **DoD:** ghi lại ≥5 câu in‑scope, 0 câu bắn sentinel nhầm.
- [x] 4.2 Bộ câu **out‑of‑scope** hỏi khi đang mở một bài (đáp án ở tin khác): khẳng định bắn sentinel → mở rộng → 2 lượt → trả lời grounded trên tin đúng, citation mở đúng. **DoD:** ghi lại dãy, xác nhận citation trỏ tin thật (bấm thử), không phải bịa từ bài đang mở.
- [x] 4.3 Đo tần suất `mode="expanded"` qua `chat_logs` trên bộ thử — tín hiệu prompt có quá nhạy không. **DoD:** ghi tỉ lệ bắn sentinel; nếu cao bất thường trên bộ in‑scope thì chỉnh prompt (task 1.1) rồi đo lại.

## 5. Tài liệu (làm sau khi code đã chạy)

- [x] 5.1 `CLAUDE.md` mục chat: ba scope (Bài / Mở rộng‑tự‑động / Toàn hệ thống); cơ chế **sentinel + lượt gọi 2** (không classifier, không `response_schema`); trần 2 lượt là chỗ dùng của hằng số để‑dành; v1 mở rộng bằng keyword, recall đầy đủ chờ ⑥. **DoD:** người đọc hiểu vì sao câu mở rộng tốn 2 lượt và độ trễ gấp đôi.
- [x] 5.2 Ghi rõ badge scope hai chiều thay khuyết bỏ‑chip một‑chiều của ①. **DoD:** không ai tưởng chip cũ vẫn là cơ chế chuyển scope.
