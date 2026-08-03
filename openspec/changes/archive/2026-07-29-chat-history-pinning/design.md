## Context

**Module: M8 (Chat Q&A).** Không đụng M1–M7, không đụng delivery/n8n, **không thêm/sửa bảng DB
nào** — đây thuần tuý là thay đổi cách dựng context trong bộ nhớ.

`chat-context-depth` bỏ cô lập luồng theo scope và thay bằng bất biến: *mọi tin được nhắc
trong history đều còn mặt trong ngữ cảnh lượt hiện tại*. Bất biến đó hiện chỉ là lời hứa —
`grep history` trong `chat_service.py` cho thấy `history` chỉ chảy vào `_history_block` →
prompt, **không chạm** `_rank`, `_question_terms`, hay embedding.

Số đo 29/07/2026 (`_rank` là hàm thuần nên đo được miễn phí):

| Phép đo | Kết quả |
|---|---|
| Cặp (tin đã bàn, chủ đề mới) rơi khỏi top-60 | **47/90 = 52%** |
| Hạng tệ nhất quan sát được | 118/179 |
| History đầy trần (5 lượt hỏi–đáp) chiếm | 1.713 / 45.228 ký tự = **3,8%** prompt |
| Một dòng index nén | ≈ 366 ký tự |

Ràng buộc kế thừa, không được phá:
- `build_context()` là **hàm thuần** (không DB, không model, không đọc `settings`) — RS harness
  chạy offline/miễn phí dựa vào điều này.
- `index_limit` là **TỔNG** số tin vào prompt, ô sâu tính trong đó.
- Prompt **không chứa UUID**; model chỉ thấy số `[n]`, server giữ bảng ánh xạ.
- Đoạn thân bài xếp hạng, **insight** mới là đích của citation.

## Goals / Non-Goals

**Goals:**
- Tin đã trích trong history có mặt trong index lượt hiện tại, tất định, không phụ thuộc `_rank`.
- Chi phí token = 0, lượt gọi model = 0, không chốt lại baseline RS.
- Cái giá (mất đuôi top-K) đo được trước khi viết code.

**Non-Goals:**
- Nén/tóm tắt history (bác bỏ — xem proposal).
- Sửa `_rank`/RRF/`_relevance`.
- Ghim vào ô sâu.
- Tự thêm vào working set.
- Rerank cross-encoder (change riêng, làm **sau** cái này).

## Decisions

### D1 — Bất biến phải được **thu hẹp**, không phải thực thi nguyên văn

Bất biến như `chat-context-depth` viết ra là **không thực thi được**. History đầy có thể nhắc
tới ~25 tin (5 lượt trả lời × tối đa 5 citation). Ghim 25 chỗ ⇒ K hiệu dụng còn 35 ⇒ RS đo
được recall@K tụt 0,968 → 0,954 (gãy từ K=53). Nên chọn: **giữ recall, thu hẹp lời hứa**.

Bất biến mới, đúng với thứ code làm được:

> **N tin được trích GẦN NHẤT trong history luôn có mặt trong index của lượt hiện tại.**

Đây là điều chỉnh thật sự về ngữ nghĩa, không phải diễn đạt lại — spec phải ghi rõ, nếu không
lần sau lại có người đọc bất biến cũ rồi tưởng nó đúng toàn phần.

*Đã cân nhắc:* ghim toàn bộ tin trong history → loại vì phá recall. Ghim theo điểm liên quan →
loại vì đó là heuristic đoán ý định, đúng loại lỗi repo này đã trả giá nhiều lần
(`_roles_in_question` khớp chuỗi con, `_CAPABILITY_PHRASES` code chết).

### D2 — Ghim **trong** `chat_index_top_k`, đẩy đuôi bảng ra

Giữ nguyên bất biến ngân sách token. 60 tin vẫn là 60 tin, chỉ khác N trong số đó do history
chỉ định thay vì `_rank`.

Đo trước bằng RS harness (`CHAT_INDEX_TOP_K` truyền qua env, harness đọc từ settings):

| Số chỗ ghim | K hiệu dụng | recall@K | recall@5 | Kết luận |
|---|---|---|---|---|
| 3 | 57 | 0,968 = baseline | 0,900 = baseline | ✅ biên **3 hạng** |
| 5 | 55 | 0,968 | 0,900 | ⚠️ biên 1 hạng |
| 6 | 54 | 0,968 | 0,900 | biên 0 — sát vách |
| 7 | 53 | **0,954** ▼ | 0,900 | ❌ gãy |

Vách nằm ở **hạng 54** (một `must_have` đứng đó). Hạng 21–53 rỗng. **recall@5 không đổi ở mọi
mức K xuống tận 10** — xác nhận ghim ở đuôi không chạm phần đầu bảng.

*Đã cân nhắc:* ghim **ngoài** K (cộng thêm dòng) → +2,4% prompt với 3 chỗ. Loại vì phá bất
biến "index_limit là TỔNG", và vì đo cho thấy trong-K miễn phí.

### D3 — N = 3, cấu hình qua `CHAT_HISTORY_PIN_SLOTS`

Trùng số với `chat_deep_slots` (3) và `MAX_REFS` (3) — hệ thống chỉ có một con số "3" thay vì
ba con số phải nhớ riêng. Biên an toàn 3 hạng theo D2.

**Luật kèm theo, phải ghi vào CLAUDE.md:** đổi số chỗ ghim ⇒ **bắt buộc** chạy lại RS harness.
Vách hạng 54 là một điểm dữ liệu trên corpus 179 tin — nó không phải hằng số của hệ thống.

### D4 — Tin ghim đặt ở **CUỐI** index, không phải đầu

`CHAT_SYSTEM_PROMPT` dặn model *"tin ở đầu danh sách đáng chọn hơn"*. Tin ghim theo định nghĩa
**không liên quan tới câu hỏi lượt này** — nó có mặt để làm chỗ dựa cho tham chiếu trong
history, không phải để làm câu trả lời. Đặt ở đầu là dạy model ưu tiên chủ đề cũ.

Hệ quả: đánh số `[n]` của tin ghim là các số **cuối dãy**. Vẫn một dãy liên tục, vẫn một
`mapping` — không đụng bất biến của `chat-citation-integrity`.

### D5 — Khử trùng theo `insight.id` trước khi ghim

Phần lớn trường hợp tin đã bàn vẫn còn trong top-K (ma trận đo: nhiều ô có hạng 4–17). Ghim
mà không khử trùng ⇒ cùng một tin có **hai số** ⇒ đúng cái bẫy "hai hệ quy chiếu cho `n`" mà
`chat-citation-integrity` đã phải sửa. Khử trùng trước, rồi mới lấp cho đủ N.

Hệ quả tốt: số tin thật sự bị đẩy khỏi đuôi thường **ít hơn N**.

### D6 — Client gửi `insight_id` trong `TurnCitation`

`schemas/chat.py` hiện ghi: *"Chỉ mang `n` + `title` — không mang `insight_id`/`source_url`:
mọi thứ thừa hơn thế là bề mặt tấn công cho client tự khai định danh."* Change này **đảo** ghi
chú đó, và cần lý do rõ ràng:

Ranh giới tin cậy **không đổi**. `ChatRequest.referenced_insight_ids` đã nhận id thẳng từ
client (cap 20) và `_load_refs` bỏ lặng lẽ id không tồn tại. Client vì thế **đã có** khả năng
đưa insight vào context; nó chỉ không có khả năng đưa **văn bản tuỳ ý** vào — và điều đó vẫn
đúng sau change này, vì id vẫn phải tra ra một insight `published` + `is_primary` thật.

*Đã cân nhắc:* server tra ngược theo `title` → loại. Title không bảo đảm duy nhất, khớp chuỗi
là phép mờ, và một lần tra nhầm sẽ ghim sai tin **trong im lặng** — hỏng nặng hơn hẳn cái nó
tránh.

**Ràng buộc bắt buộc:** id ghim đi qua đúng đường lọc như `_load_refs` (`published` +
`is_primary`), không phải một đường nạp thứ hai.

### D7 — `build_context()` vẫn phải THUẦN

Tin ghim truyền vào dưới dạng **tham số** `pinned: list[Insight]` (đã nạp sẵn), không phải id
để hàm tự query. Nếu không, RS harness mất khả năng chạy offline — và đó là lưới duy nhất bắt
hồi quy `_rank`.

## Risks / Trade-offs

- **Model lạc đề vì 3 dòng tin cũ trong context** → RS **không** bắt được (nó đo truy hồi, không
  đo câu trả lời).
  ⚠️ **SỬA 29/07/2026 — `chat_answer_harness --live` cũng KHÔNG bắt được.** Bản đầu của mục này
  ghi "bắt buộc `--live`" như thể nó phủ được ca này. Sai: `chat_scenarios.jsonl` có **0/98
  kịch bản mang `history`**, nên lượt `--live` **không bao giờ đi qua đường ghim**. Nó chứng
  minh *không hồi quy trên đường cũ* (vẫn phải chạy — change sửa `build_context` và
  `_load_refs`), không chứng minh *ghim vô hại*.
  Lưới thật là một bộ đo **hội thoại hai lượt** qua endpoint thật, đo hai mặt: (a) hỏi chủ đề
  MỚI có bị tin ghim kéo đi không; (b) hỏi QUAY LẠI tin đã bàn có trả lời được không. Đo được:
  **0/4** lạc đề · **2/2** trả lời được. Chi tiết ở `measurement.md` §5.3.
- **Biên 3 hạng là mỏng và phụ thuộc corpus** → ghi luật "đổi số chỗ ghim ⇒ chạy lại RS" vào
  CLAUDE.md; corpus lớn lên thì đo lại.
- **Bất biến bị thu hẹp, tin nhắc từ lâu vẫn rơi** → nói thẳng trong spec thay vì để lời hứa
  cũ đứng đó sai. Người dùng còn working set làm lưới cho tin muốn giữ lâu.
- **Proxy của phép đo 52%** (top-3 của `_rank` thay cho "tin model thật sự đã trích") → con số
  có thể lệch; nhưng hướng và độ lớn đủ rõ để quyết định, và ca thật chỉ tệ hơn chứ không nhẹ hơn.
- **Đường `expanded` đánh số từ `start=2`** → tin ghim phải nối tiếp đúng dãy đó, không được
  giả định bắt đầu từ 1.

## Migration Plan

Không có migration DB. Không có cờ bật/tắt runtime ngoài `CHAT_HISTORY_PIN_SLOTS`; đặt **0**
là tắt hoàn toàn và hệ thống trùng khít hành vi hiện tại — đó cũng là đường rollback.

Client cũ không gửi `insight_id` trong `TurnCitation` ⇒ không có gì để ghim ⇒ hành vi như cũ.
Suy giảm êm, không cần đồng bộ phiên bản FE/BE.

## Open Questions

1. Ghim có nên bỏ qua tin đã nằm trong **working set** không? (Chúng đã ở ô sâu, ghim thêm là
   thừa — nhưng khử trùng ở D5 có thể đã xử lý.)
2. Khi history nhắc >N tin, có nên phát `status` cho người dùng biết tin nào đang được giữ
   không? Nghiêng **không** — status ở `chat-context-depth` đã mang tên 2 tin đọc kỹ, thêm nữa
   là nhiễu.
3. `MAX_HISTORY_TURNS = 10` là 10 **tin nhắn** = 5 lượt hỏi–đáp, trong khi To-Be viết "10 lượt
   hội thoại". Có nên nâng lên 20 tin nhắn khi history chỉ chiếm 3,8% prompt? Ngoài scope
   change này nhưng đáng ghi lại.
4. **Bộ đo hội thoại hai lượt có nên vào bộ đo thường trực không?** Hiện nó là script ở
   scratchpad, chạy tay. Nó là lưới **duy nhất** chạm đường ghim — `chat_answer_harness` có
   0/98 kịch bản mang history nên vĩnh viễn không với tới. Hai cách: thêm trường `history` vào
   `chat_scenarios.jsonl` (gán nhãn tay, tốn công, nhưng dùng lại được toàn bộ hạ tầng chấm
   điểm), hoặc giữ script riêng. Chưa quyết — nhưng **đừng để trạng thái hiện tại kéo dài**,
   vì lần sửa `build_context` tiếp theo sẽ không có gì canh.
