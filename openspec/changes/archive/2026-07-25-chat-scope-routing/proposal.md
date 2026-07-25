# Proposal: chat-scope-routing

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — phủ phần 7 khung To‑Be: Triple Scope & Dynamic Routing).

## Why

Ranh giới hai chế độ hiện tại là **hai cực đoan cứng**: có `insight_id` → 100% bài đang xem (mode B), vắng
→ 100% toàn cục (mode A). Không có đường ở giữa. Hệ quả là **Scope Paradox** trong báo cáo To‑Be: đang mở
bài B mà hỏi câu vượt phạm vi ("so với tin Nvidia lúc nãy thì bài này thế nào?", "gần đây có tin sa thải
nào không?") thì mode B chỉ đọc dữ liệu **một** bài B (`_answer_insight` select đúng một insight) → trả
lời cụt "bài này không đề cập", dù toàn hệ thống có tin đúng.

`chat-context-isolation` (①) cố ý **không** gánh ca này — nó gỡ đường trả‑lời‑từ‑history‑cũ (ungrounded) và
để lại một **ngõ cụt trung thực**. Change này đóng nốt ngõ cụt đó bằng cách cho mode B **tự mở rộng sang
toàn hệ thống** khi bí, và cho người dùng **chuyển phạm vi tường minh** khi muốn.

## What Changes

- **Ba scope phạm vi**: *Bài đang xem* (mode B, giữ nguyên) · *Mở rộng* (bài B + toàn cục, MỚI, tự động) ·
  *Toàn hệ thống* (mode A, giữ nguyên).
- **Trigger 1+2 (chốt 23/07/2026)**:
  - **(1) Toggle phạm vi tường minh** — badge chỉ báo scope hiện tại trên trang chi tiết, chuyển đổi hai
    chiều *Bài đang xem ↔ Toàn hệ thống* bằng 1‑click, **0 lượt gọi thêm** (đi qua việc gửi/không gửi
    `insight_id` sẵn có). Sửa luôn khuyết của ①: bỏ chip hiện là **một chiều**, badge cho **quay lại** bài.
  - **(2) Auto‑fallback bằng lượt gọi thứ 2** — lượt gọi mode B phát một **sentinel văn bản thuần** khi câu
    hỏi rõ ràng ngoài phạm vi bài; server thấy sentinel thì dựng context mở rộng (bài B + index toàn cục) và
    gọi model lần hai để trả lời **có căn cứ**, `mode="expanded"`. Dùng đúng trần `MAX_MODEL_CALLS_PER_QUESTION=2`
    **vốn để dành cho đúng việc này**. **Không** thêm call classifier riêng — dùng phán đoán của chính model
    trả lời B.
- **Đánh dấu câu trả lời mở rộng** trên widget để người dùng biết nó tìm toàn hệ thống chứ không chỉ bài.

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-qa-service`: chế độ per‑insight SHALL tự mở rộng sang scope toàn cục khi câu hỏi ngoài phạm vi bài,
  qua sentinel + lượt gọi thứ hai, trong trần 2 lượt.
- `chat-web-widget`: widget SHALL hiển thị chỉ báo phạm vi và cho chuyển scope hai chiều; SHALL đánh dấu
  câu trả lời được mở rộng tự động.

## Non-goals

- **Không** để người dùng chọn scope "Mở rộng" bằng tay — scope giữa chỉ sinh ra **tự động** qua fallback;
  toggle tường minh là nhị phân (bài ↔ toàn hệ thống). (design D1)
- **Không** dùng `response_schema` cho sentinel (giữ bài học `gemini-structured-output` — output dài + schema
  = runaway). Sentinel là token văn bản thuần server tra, cùng tinh thần marker `[n]`.
- **Không** dùng heuristic tiền‑kiểm (trùng từ khoá) làm trigger — mong manh; đã loại ở fork (cơ chế 3).
- **Không** thêm vector search — v1 mở rộng bằng keyword‑rank toàn cục như mode A; chất lượng ngữ nghĩa đầy
  đủ khi `chat-hybrid-retrieval` (⑥) land (dependency mềm, design D6).
- **Không** thêm streaming — độ trễ khi mở rộng gấp đôi (2 lượt) là thật; che bằng ⑤ sau.

## Dependencies

- **`chat-context-isolation` (①) — cứng, land TRƯỚC**: badge chuyển scope = đổi scopeKey = đổi luồng hội
  thoại; xây trên mô hình cô lập của ①. Delta widget của change này viết trên trạng thái **sau ①**.
- **`chat-hybrid-retrieval` (⑥) — mềm**: v1 chạy không cần ⑥; recall của phần mở rộng đầy đủ khi có ⑥.
- `chatbot-qa` (archive 22/07/2026) — sửa prompt mode B + mode routing thuộc code của change đó.

## Impact

- **Backend**: `ai/prompts.py` (sentinel trong prompt mode B), `services/chat_service.py` (phát hiện sentinel
  → dựng context mở rộng → lượt 2 → `mode="expanded"`), test mới.
- **Frontend**: `components/ChatWidget.tsx` (badge scope hai chiều, nhãn câu trả lời mở rộng), `api/chat.ts`
  (đọc `mode`), test.
- **Docs**: `CLAUDE.md` mục chat — ba scope + cơ chế sentinel + trần 2 lượt.
- **Không** migration, không đổi shape request/response (chỉ thêm giá trị `mode="expanded"`).
