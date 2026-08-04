## Context

Báo cáo kiến trúc To‑Be (`docs/ignored/chatbot_qa_architecture_analysis.md`, Nguy hiểm #3) mô tả một chế
độ hỏng: người dùng trên dashboard đổi bài liên tục, còn Client gửi mù 10 lượt history của bài cũ. Soi
code thật thì đúng như vậy, và nghiêm trọng hơn một chút so với báo cáo — history **không giới hạn ở bài
cũ**, nó tích luỹ qua *mọi* ngữ cảnh trong phiên:

```
ChatWidget.tsx:43   messages: Message[]              ← một mảng cho cả phiên, không bao giờ reset
ChatWidget.tsx:54   activeInsightId = contextDropped ? null : routeInsightId
ChatWidget.tsx:115  history = messages.filter(!isError)   ← lấy TẤT CẢ, bất kể thuộc scope nào
ChatWidget.tsx:121  mutation.mutate({ question, history, insight_id: activeInsightId })
```

Chip đã theo route (`useMatch('/insights/:id')` + reset `contextDropped` khi đổi bài), nhưng `messages`
thì không — nên `insight_id` đúng scope mới trong khi `history` vẫn là scope cũ. Câu nối tiếp mập mờ là
nơi lỗi biểu hiện: server (mode B) đọc bài B, model đọc history nói về bài A.

**Module ảnh hưởng:** M8 (Chatbot/Search) — thuần frontend widget.
**API endpoints:** `POST /api/v1/chat` — **không đổi** request/response. Vẫn nhận `history` (≤10 lượt),
vẫn stateless. Thay đổi nằm ở *widget quyết định gửi lượt nào*.
**Bảng DB:** không đụng, không migration.
**AI/LLM:** không gọi thêm model, không sửa prompt. Chất lượng resolve ngữ cảnh cải thiện vì input sạch
hơn, không vì đổi model.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- `history` gửi lên **chỉ** chứa lượt của scope hiện tại — biến bất biến này thành thứ test được.
- Đổi scope không mất hội thoại cũ: quay lại scope trước thấy lại đúng luồng của nó (sub‑thread).
- Dựng test frontend đầu tiên khoá đúng chế độ drift, không dựng bộ test nặng.

**Non-Goals:**
- Không nén/tóm tắt history (cần model → `chat-intent-router`).
- Không thêm scope giữa / auto‑fallback (`chat-scope-routing`).
- Không đổi backend, không đổi grounding/citation/quota.

## Decisions

### D1 — Cô lập bằng **tách luồng theo scope**, không phải xoá khi đổi

Hai cách đạt bất biến "history sạch theo scope":

| | Xoá `messages` khi đổi scope | Tách luồng theo scope (chọn) |
|---|---|---|
| History sạch | ✅ | ✅ |
| Quay lại bài A thấy lại hỏi‑đáp cũ | ❌ mất | ✅ giữ |
| Khớp mô tả báo cáo ("cô lập thành sub‑thread riêng") | ❌ | ✅ |
| Độ phức tạp | thấp nhất | thấp (một map keyed theo scope) |

Chọn tách luồng: giữ `Record<scopeKey, Message[]>`, `scopeKey = activeInsightId ?? "__global__"`. Widget
render và gửi history theo luồng của `scopeKey` hiện tại. Chi phí thêm gần như bằng 0 và bám đúng ý báo
cáo. Xoá‑khi‑đổi vẫn là cài đặt **hợp lệ** với spec (bất biến giống nhau) nhưng UX kém hơn — spec khoá bất
biến, task chọn tách luồng.

*Đã cân nhắc:* lưu luồng xuống `localStorage`. Bỏ — spec hiện tại đã nói hội thoại chỉ sống "trong phiên",
đừng mở rộng vòng đời state ở change vá lỗi.

### D2 — "Toàn cục" là **một** scope, không phải "không scope"

`activeInsightId = null` (rời detail, hoặc bỏ chip) là một scope thật với luồng riêng, key `"__global__"`.
Nếu coi nó là "không scope" và dồn chung, thì hỏi toàn cục sẽ nhiễm history của lần hỏi toàn cục *trước
đó về chủ đề khác* — đỡ nặng hơn ca A→B nhưng vẫn là drift. Một scope, một luồng, nhất quán.

### D3 — Bỏ chip (✕) tính là đổi scope; đổi bài A→B cũng vậy

`contextDropped` đổi `activeInsightId` từ `routeInsightId` sang `null` → đổi `scopeKey` → đổi luồng. Nhờ D2
điều này rơi tự nhiên: bấm ✕ để "hỏi toàn cục" mở luồng `__global__` sạch, không kéo theo hỏi‑đáp về bài
đang mở. Đây chính là ca "Xung đột Mức 2" trong sơ đồ Scope Paradox của báo cáo.

### D4 — Test cắt qua state, phủ đúng chuỗi thao tác gây drift

Repo chưa có test frontend. Dựng tối thiểu (cùng khung mà `chat-citation-integrity` 2.4 cần — điều phối để
một change dựng, change kia dùng lại). Test khẳng định trên **payload gửi đi**, không trên UI:

- A→B→A: hỏi ở A, chuyển B, kiểm `history` gửi ở B **không** chứa lượt A; quay lại A thấy lại luồng A.
- Bỏ chip: đang ở bài, bấm ✕, hỏi — `history` **không** chứa lượt về bài, `insight_id` vắng.
- Rời detail: từ bài về danh sách, hỏi — `history` là luồng toàn cục, không phải luồng bài.

## Risks / Trade-offs

- **[Người dùng mong history "liền mạch" xuyên bài]** → Thực ra ngược lại: gộp xuyên bài mới là hành vi gây
  hại đang có. Nếu cần "hỏi về cả A lẫn B" thì đó là câu toàn cục, chạy ở scope `__global__` với dữ liệu
  cả kho — đúng đường, không cần history bài.
- **[Tách luồng làm state phức tạp hơn]** → Chỉ một map + selector; không thêm thư viện, không store mới
  (dự án dùng React state + TanStack Query, không thêm Zustand cho việc này).
- **[Hai change cùng dựng test frontend]** → Điều phối trong Dependencies: change land trước dựng runner
  (`npm test`, một lệnh, không trình duyệt), change sau thêm case. Không chồng lấn vùng code.
- **[Backend vẫn nhận history mù]** → Chấp nhận ở change này: backend vẫn stateless và tin client. Phòng
  thủ chiều sâu phía server (reformulator gộp history vào truy vấn độc lập) thuộc `chat-intent-router`.

## Migration Plan

1. Frontend: chuyển `messages` thành luồng‑theo‑scope; `send()` lấy history theo `scopeKey`; render theo
   luồng hiện tại.
2. Dựng test runner frontend tối thiểu + 3 ca drift ở D4.
3. Docs: thêm dòng gotcha vào `CLAUDE.md`.

Rollback: không migration, không đổi API/dữ liệu — revert commit là đủ. Đây là fix state phía client.

## Open Questions

- **Cố ý hỏi về insight KHÁC khi đang ở mode B** ("so với bài Nvidia lúc nãy thì bài này thế nào") — change
  này **cố ý không gánh**. Mode B chỉ nạp dữ liệu của **một** insight (`_answer_insight` select đúng
  `insight_id`); A không bao giờ có trong dữ liệu gửi model, chỗ duy nhất A từng "xuất hiện" là text history
  cũ — trả lời từ đó chính là ungrounded mà change này gỡ. Nhu cầu này tách hai: (a) *tiếp tục trò chuyện A*
  → điều hướng về trang A, luồng A khôi phục (D1 đã lo); (b) *kéo dữ liệu thật của A vào câu trả lời ở B* →
  cần retrieval toàn cục/mở rộng, **thuộc `chat-scope-routing` (③)** auto‑fallback. Giai đoạn sau ① trước ③
  là **ngõ cụt trung thực** ("bài này không nói về A") — đúng hơn hôm nay nhưng UX kém hơn cho tới khi ③ vá.
  Đừng nới scope B để "chữa" ca này ở đây.
- **Giữ luồng cũ bao lâu trong phiên?** v1 giữ toàn bộ luồng trong bộ nhớ phiên (đóng/mở widget không mất).
  Nếu phiên rất dài, nhiều bài, có thể giới hạn số luồng giữ — để lại khi có tín hiệu thật.
- **Hiển thị cho người dùng biết đây là luồng riêng của bài?** Có thể thêm gợi ý nhỏ khi đổi scope mà luồng
  mới rỗng ("Bắt đầu hỏi về bài này…"). Thuộc UX, cân nhắc ở `chat-scope-routing` cùng badge scope.
