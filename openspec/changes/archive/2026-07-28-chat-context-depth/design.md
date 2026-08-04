# Design: chat-context-depth

**Module:** M8 (Chatbot/Search). **Model:** không đổi — `gemini-2.5-flash` cho trả lời,
`text-multilingual-embedding-002` cho embedding. **Grounding:** giữ nguyên D4 — server cấp phát số, model
chỉ đánh dấu; prompt KHÔNG chứa UUID.

## Sơ đồ

```
CLIENT                                    SERVER
─────────────────────────────────         ────────────────────────────────────────────────
working set (chip)                        build_context(refs, ranked, k_deep=3)
  [Gemma 4 12B    ×]                        ┌──────────────────────────────────────────┐
  [DiffusionGemma ×]  ──refs──▶             │ Ô SÂU  [1] ghim #1  (7 field + bài gốc)  │
                                            │        [2] ghim #2  (7 field + bài gốc)  │
question ────────────────────▶              │        [3] top‑rank (7 field + bài gốc)  │
history (marker→tiêu đề) ────▶              ├──────────────────────────────────────────┤
                                            │ INDEX  [4..60] 115 token/tin, đã loại ô sâu│
                                            └──────────────────────────────────────────┘
                                                        MỘT bảng ánh xạ n → insight
```

## Quyết định thiết kế

### D1 — Ô sâu lấp tất định, KHÔNG đoán ý định
3 ô, lấp bằng `referenced_insight_ids` theo thứ tự, còn dư thì lấp bằng đầu danh sách `_rank`. Không có
nhánh "câu này có vẻ cần chi tiết → hydrate". Lý do: mọi heuristic phân loại câu hỏi ở repo này đều đã
phải trả giá (`_roles_in_question` khớp chuỗi con, `_CAPABILITY_PHRASES` code chết). Lấp tất định làm
`build_context` là **hàm thuần** ⇒ RS harness đo được offline, miễn phí.

Hệ quả đo được: câu toàn cục thuần (0 ref) tự động có 3 bài sâu nhất — đó chính là ②′ hydration, và nó
chữa 4/5 ca từ chối sai mà **không cần** ai bấm gì.

### D2 — Ngân sách token
Đo thật trên fixture: ô sâu 1.527–3.466 token/bài (raw content chiếm 58–76%), index 115 token/tin.
Xấu nhất `3 × 3.466 + 57 × 115 = 16,9k` — dưới mức ~19k mà production đã chạy từ `chatbot-qa`.
`k_deep` là settings (`CHAT_DEEP_SLOTS`, mặc định 3), hạ được nếu corpus có bài dài hơn.

⚠️ **Đừng hạ `k_deep` để tìm tốc độ**: bài học `chat-latency-thinking-budget` — cắt ngữ cảnh 76% chỉ giảm
độ trễ 33%; ~90% độ trễ nằm ở lượt gọi model. Đo ở spike C1: thêm 2 ô sâu = **+50ms**.

### D3 — MỘT luồng: đảo ngược `chat-context-isolation` có chủ đích
Bất biến cũ: "history cô lập theo scope", sinh ra để chặn Nguy hiểm #3 (đổi bài A→B rồi hỏi "nó" →
history nói A, context là B → model resolve sai). Đó là một **mâu thuẫn** giữa hai nguồn.

Với working set, cả A lẫn B **đều nằm trong context**, mỗi bài một số. Bài toán chuyển từ *mâu thuẫn*
sang *khử nhập nhằng bình thường* — thứ model làm được. Chế độ hỏng cũ sinh ra **từ chính việc tách đôi**.

Bất biến cũ được **thay**, không phải xoá:
> Mọi bài được nhắc tới trong history SHALL còn mặt trong context của lượt hiện tại, hoặc dưới dạng ô sâu,
> hoặc trong index.

`ChatWidget.drift.test.tsx` viết lại quanh bất biến mới. **Không được xoá file rồi đi tiếp.**

### D4 — Marker history giải thành tiêu đề
Đây là bug **đang tồn tại**, không phải rủi ro mới: `_history_block()` dump nguyên văn câu trả lời cũ kèm
`[3]`, trong khi mỗi lượt `_rank` dựng bảng ánh xạ mới ⇒ `[3]` lượt trước và `[3]` lượt này là hai tin khác
nhau, model đọc hai nghĩa của một số.

Phương án chọn: server thay marker trong history block bằng `[«tiêu đề»]`. Giữ được ngữ nghĩa tham chiếu,
không tạo hệ quy chiếu số thứ hai.

Đã loại: (a) *đánh số ổn định theo luồng* — server stateless, sổ đánh số phải do client giữ và gửi lên,
tức là thêm một nguồn sự thật client kiểm soát được, đúng thứ D4 gốc tránh; (b) *xoá sạch marker khỏi
history* — mất luôn khả năng hiểu "so sánh [1] với [2] ở trên".

### D5 — Sentinel/expanded giữ nguyên cho đường cũ
Khi có `referenced_insight_ids`, context **đã** mang cả ô sâu lẫn index toàn cục ⇒ không còn gì để "mở
rộng" ⇒ **một lượt gọi**, không sentinel. Câu ngoài phạm vi bài ghim vẫn trả lời được từ index.

Đường `insight_id` cũ (không refs) giữ mode B + sentinel + expanded cho client cũ,
`chat_answer_harness` (17 kịch bản `expanded`), và test hiện có. Gộp hai đường là change sau.

⚠️ **Sửa sau khi implement — "nguyên xi" là quá mạnh.** Đường expanded nay đi qua `build_context`
với `k_deep=1`, và vì `index_limit` đếm **cả** ô sâu (xem D1) nên phần index có **59** dòng thay vì
60. Ngữ nghĩa mới đúng hơn — trần top-K phải là trần thật, không thì nó là lời nói suông đúng ở cấu
hình chặt nhất — nhưng nó **có** đổi hành vi đường cũ một chút. Đo `--live` 28/07: không kịch bản
`expanded` nào tụt vì lý do này (3 ca tụt AnsRel đều là judge chấm P cho câu trả lời đúng).

⚠️ **Đường legacy có một khuyết tật, và nó đã dẫn tới một phép đo sai** (đóng 28/07): prompt mở rộng
mở đầu bằng *"Bài bạn đang xem không nhắc tới điều này"* — sai ngữ cảnh cho câu SO SÁNH, vì bài đang
xem chính là một vế. Bốn kịch bản `comparison_expanded` vì thế chỉ đạt AnsRel 0,62 — nhưng chúng đang
mô tả một luồng **người dùng không còn đi**: widget luôn đưa bài đang xem vào working set.

Đã chuyển sang đường thật (`mode=focused`, `referenced_insight_ids=[bài đang xem]`, nhóm đổi tên
`comparison_in_article`): **AnsRel 0,62 → 1,00**, riêng `cmp-gemma-expanded` 0,00 → 1,00. Đường legacy
vẫn còn trong code và vẫn có 13 kịch bản `expanded` canh nó — cái bỏ đi chỉ là việc dùng nó để mô tả
một luồng đã chết.

⇒ `mode` trong `chat_logs` thêm giá trị **`focused`** (có refs). `meta`/`insight`/`global`/`expanded` giữ nguyên nghĩa.

### D6 — Prompt cho phép hình dạng so sánh
`CHAT_SYSTEM_PROMPT` hiện chốt "Mỗi tin gói trong MỘT gạch đầu dòng, tối đa 2 câu" — cấm đúng hình dạng
một câu trả lời đối chiếu. Khi ≥2 ô sâu, prompt SHALL nới: cho phép đối chiếu theo chiều (mục đích, kiến
trúc, tài nguyên, hiệu năng, ứng dụng) thay vì mô tả song song. Trần "TỐI ĐA 5 tin" giữ nguyên.

⚠️ Sửa `CHAT_SYSTEM_PROMPT` ⇒ **bắt buộc** `chat_answer_harness --live` trước khi merge.

### D7 — Giới hạn và suy giảm êm
- `referenced_insight_ids` quá `CHAT_DEEP_SLOTS` → lấy N đầu, bỏ phần dư (không lỗi).
- Ref trỏ insight không tồn tại/không `published` → **bỏ qua lặng lẽ**, không 404: người dùng có thể ghim
  một tin rồi tin đó bị unpublish, và làm hỏng cả câu hỏi vì một chip cũ là đổi sai.
- Ref rỗng/vắng → hành vi **trùng khít** hôm nay cộng hydration top‑3.

## API

`POST /api/v1/chat` và `POST /api/v1/chat/stream` — thêm field optional:

```jsonc
{
  "question": "so sánh hai cái này",
  "history": [...],
  "insight_id": null,                    // giữ nguyên, đường cũ
  "referenced_insight_ids": ["uuid-A", "uuid-B"]   // MỚI, tối đa CHAT_DEEP_SLOTS
}
```

Response không đổi hình dạng; `mode` có thêm giá trị `focused`.

## DB

**Không migration.** Không bảng/cột mới. Đọc thêm `raw_documents.normalized_content` cho ô sâu — quan hệ
đã có, chỉ cần `selectinload` trong `list_for_chat` hoặc một truy vấn phụ theo id.

## Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Prompt phình gần trần | `CHAT_DEEP_SLOTS` là settings; đo thật 16,9k xấu nhất |
| Đảo `chat-context-isolation` làm sống lại context poisoning | bất biến thay thế ở D3 + test viết lại |
| Nới prompt làm tụt Faithfulness | ngưỡng gate ≥0,95 giữ nguyên; `--live` bắt buộc |
| Ghim sai bài (chip cũ) | bỏ chip 1 click; ref chết bỏ qua lặng lẽ (D7) |
