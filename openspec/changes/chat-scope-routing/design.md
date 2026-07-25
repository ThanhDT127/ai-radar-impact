## Context

Báo cáo To‑Be mục 3.2 #1 đề xuất **Triple‑Scope & Dynamic Routing** để gỡ Scope Paradox (mục 2.3): thay
ranh giới nhị phân cứng bằng ba phạm vi, với auto‑fallback và chỉ báo scope tường minh. Hiện trạng code:
`_answer_insight` (`chat_service.py:171`) nạp **đúng một** insight; mode B không có đường thoát khi câu hỏi
vượt phạm vi bài. `chat-context-isolation` (①) đã gỡ đường ungrounded (trả lời từ history bài khác) và để
lại ngõ cụt trung thực — change này đóng nốt.

Fork cơ chế trigger đã chốt (23/07/2026): **1+2** — toggle tường minh làm nền tin cậy, auto‑fallback bằng
lượt gọi thứ 2 làm tầng thông minh. Loại cơ chế 3 (heuristic tiền‑kiểm) vì mong manh.

**Module ảnh hưởng:** M8 (Chatbot/Search) — backend (prompt + service) + frontend (widget).
**API endpoints:** `POST /api/v1/chat` — request/response **không đổi shape**; thêm giá trị `mode="expanded"`
(`mode` là `str` tự do → tương thích ngược).
**Bảng DB:** không đụng, không migration. `chat_logs` ghi `model_calls=2` cho câu mở rộng.
**AI/LLM:** Gemini 2.5 Flash qua Vertex. Sửa **prompt mode B** để định nghĩa sentinel out‑of‑scope (văn
bản thuần, **không** `response_schema`). Grounding, hợp đồng `n`, fail‑closed giữ nguyên. **Không** thêm
call classifier — tín hiệu out‑of‑scope là byproduct của lượt gọi trả lời B.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Đóng ngõ cụt của mode B: câu ngoài phạm vi bài được trả lời **có căn cứ** từ toàn hệ thống, không cụt.
- Người dùng chuyển phạm vi tường minh, **hai chiều**, 1‑click, không điều hướng.
- Không thêm call classifier; auto‑fallback nằm trong trần 2 lượt đã để dành.

**Non-Goals:**
- Không cho chọn scope "Mở rộng" bằng tay (D1); không `response_schema`; không heuristic trigger; không
  vector (⑥ lo recall); không streaming (⑤ lo độ trễ).

## Decisions

### D1 — Ba scope, nhưng scope giữa chỉ **tự động**

*Bài đang xem* (B) và *Toàn hệ thống* (A) là hai lựa chọn người dùng thấy được (toggle nhị phân). *Mở rộng*
(B + toàn cục) **không** phải một nút bấm — nó **sinh ra tự động** khi mode B bí. Lý do: người dùng khó
phân biệt "mở rộng" với "toàn hệ thống"; phơi ba nút làm rối. Ba scope là mô hình *bên trong*; UI chỉ hai
trạng thái + một hành vi tự động.

### D2 — Trigger 1+2

**(1) Toggle tường minh** đi qua cơ chế sẵn có: gửi `insight_id` → scope bài; không gửi → toàn cục (đúng
mô hình ① đã dựng). Change này chỉ **phơi nó thành badge** với nhãn scope rõ và **chiều quay lại** (① mới
có bỏ‑chip một chiều; badge cho *re‑enter* bài mà không cần điều hướng).

**(2) Auto‑fallback bằng lượt gọi thứ 2:** lượt gọi mode B chạy như thường; nếu câu hỏi ngoài phạm vi bài,
model phát **sentinel** thay vì bịa. Server thấy sentinel → dựng context mở rộng → gọi lần 2. Đây **không**
phải call classifier: phán đoán "câu này không nằm trong bài" là việc model đằng nào cũng làm khi cố trả
lời — ta chỉ bắt tín hiệu đó. Lượt 2 là *trả lời lại* với context rộng hơn, không phải phân loại.

### D3 — Sentinel là token văn bản thuần, phát **dè dặt**, KHÔNG `response_schema`

Prompt mode B thêm luật: *nếu câu hỏi không thể trả lời từ nội dung bài này, chỉ in đúng một dòng sentinel
`[[NGOÀI_PHẠM_VI_BÀI]]` và không gì khác.* Server: câu trả lời B là sentinel → out‑of‑scope. Không dùng
`response_schema` (bài học `gemini-structured-output`: output dài + schema = runaway JSON vỡ) — sentinel
văn bản thuần, cùng tinh thần server‑tra‑marker `[n]`.

**Phát dè dặt** (bias bất đối xứng ngược với ②):
- **Sentinel giả** (câu trả lời được từ bài nhưng model vẫn kêu ngoài phạm vi) → tốn lượt 2 vô ích + độ trễ
  gấp đôi — **tệ hơn**.
- **Thiếu sentinel** (đáng mở rộng mà không) → ngõ cụt trung thực, người dùng còn **toggle tay** (1) làm
  lưới an toàn — **nhẹ hơn**.

Nên prompt dặn: còn trả lời được **dù chỉ một phần** từ bài thì **đừng** phát sentinel. Ngược ② (② thiên
fall‑through vì gạt nhầm tệ hơn; ở đây thiên *không mở rộng* vì mở nhầm tốn 2×).

### D4 — Context mở rộng = insight bài B + index toàn cục; tái dùng retrieval sẵn có

Lượt 2 mang **cả** insight block của bài B **lẫn** index toàn cục đã xếp hạng (đúng "context‑expanded hybrid
scope" của báo cáo), để trả lời **so sánh chéo** được. Retrieval toàn cục dùng lại đúng đường mode A hiện
có (lọc published+is_primary+window → `_rank` → top‑K → index nén) và cơ chế citation `[n]`. Câu trả lời
cuối SHALL nêu rõ đã tìm toàn hệ thống ("Bài này không nhắc tới X; tìm toàn hệ thống thấy…[n]"). Citation
lấy từ mapping của lượt 2.

### D5 — Nằm trong trần 2 lượt đã để dành

`MAX_MODEL_CALLS_PER_QUESTION = 2` (`chat_service.py:46`) được để dành sẵn cho "tầng fetch‑chi‑tiết sau
này" — chính là đây. Câu mở rộng = call B + call global = **đúng 2**, chạm trần; lượt thứ 3 sẽ raise. Ghi
`chat_logs` `model_calls=2`. Budget ngày kiểm ở đầu request (như cũ); một câu mở rộng tiêu 2 đơn vị — chấp
nhận, không thêm cửa kiểm giữa chừng.

### D6 — v1 mở rộng bằng keyword‑rank; recall đầy đủ chờ ⑥

Chưa có vector, phần mở rộng xếp hạng bằng keyword như mode A → câu diễn đạt lệch từ khoá (sa thải vs
*layoff*) vẫn có thể sót. Chạy được và đúng hướng; recall ngữ nghĩa đầy đủ khi `chat-hybrid-retrieval` (⑥)
land. Khai dependency mềm, không chặn v1.

### D7 — Badge chuyển scope hai chiều, sửa khuyết một‑chiều của ①

① chỉ có bỏ‑chip (bài → toàn cục, một chiều); muốn quay lại bài phải điều hướng. Badge của change này cho
**cả hai chiều** tại chỗ. Chuyển scope = đổi `scopeKey` = đổi luồng (cô lập của ①) — nhất quán, không thêm
mô hình state mới.

## Risks / Trade-offs

- **[Sentinel bắn thừa → luôn 2 lượt]** → Prompt dè dặt (D3) + **đo bằng log** `mode="expanded"`: tần suất
  cao bất thường là tín hiệu prompt quá nhạy, chỉnh lại. Biến thứ vô hình thành đo được.
- **[Sửa prompt mode B mà chat không có eval harness]** → Chỉ `gate` có harness; chat prompt chưa. Nên phần
  xác minh (task) là **thủ công có chủ đích**: bộ câu in‑scope (không được bắn sentinel) + out‑of‑scope (phải
  bắn), chạy tay, ghi kết quả. Giữ sentinel tối giản để ít đụng hành vi trả lời thường.
- **[Độ trễ mở rộng gấp đôi 10–45s]** → Thật; lời giải là ⑤ streaming + status "Đang tìm toàn hệ thống…",
  không phải bỏ fallback. Trước ⑤, chấp nhận + badge/nhãn cho người dùng hiểu vì sao lâu.
- **[① và ③ cùng đụng scope widget]** → Dependency cứng ① trước; delta widget viết trên trạng thái sau ①.
- **[`mode="expanded"` chạm client]** → chỉ thêm giá trị `str`; widget đọc để gắn nhãn, không vỡ nếu bỏ qua.

## Migration Plan

1. Backend: thêm luật sentinel vào prompt mode B (`prompts.py`); trong `chat_service._answer_insight`, nếu
   kết quả là sentinel → gọi `_answer_global`‑mở‑rộng (insight B block + index toàn cục) → `mode="expanded"`;
   cộng dồn `_calls_used`.
2. Frontend: badge scope hai chiều (thay/nâng chip), nhãn câu trả lời `mode="expanded"`.
3. Xác minh thủ công: bộ in‑scope (không sentinel, 1 lượt) + out‑of‑scope (sentinel → mở rộng, 2 lượt, grounded
   trên dữ liệu thật). Ghi lại số.
4. Docs.

Rollback: không migration, không đổi API shape — revert commit. Bỏ nhánh sentinel thì mode B quay về cụt
như sau ①.

## Open Questions

- **Cho chọn "Mở rộng" bằng tay (badge 3 trạng thái)?** v1 không (D1). Cân nhắc nếu người dùng thường muốn
  "giữ bài + tìm thêm" chủ động.
- **Reformulator × mở rộng**: câu nối tiếp mù ở scope mở rộng cũng cần từ khoá đúng để `_rank` bắt tin — vẫn
  là bài toán của bản gộp‑từ‑khoá tất định / reformulator (hoãn, gated ⑤). Quyết cùng ⑤.
- **Ngưỡng "dè dặt" của sentinel** tinh chỉnh theo log `expanded` từ dùng thật, không đoán trước.
