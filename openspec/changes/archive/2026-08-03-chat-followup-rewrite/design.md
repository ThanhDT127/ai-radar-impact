## Context

**Module: M8 (Chat Q&A).** Không đụng M1–M7, **không thêm/sửa bảng DB nào**, **không đổi chữ ký
endpoint** — `POST /api/v1/chat` và `POST /api/v1/chat/stream` giữ nguyên request/response
schema. Đây là thay đổi bên trong tầng truy hồi.

**Model & grounding.** Lượt viết lại dùng một model rẻ (`gemini-2.5-flash-lite`, cùng bậc với
`classify_intent` của `chat-intent-hybrid-filter`), embed bằng `text-multilingual-embedding-002`
qua Vertex — **cùng model, cùng 768 chiều** với `insights.embedding` và `document_chunks`, vì
trộn hai họ vector trong một phép cosine làm lệch mà không có gì báo lỗi. **Grounding không
đổi**: bản viết lại **không đi vào prompt**, model trả lời vẫn chỉ thấy nguyên văn câu hỏi +
context có đánh số, `enforce_grounding` + `resolve_citations` chạy y như cũ. Không
`response_schema` (bài học `gemini-structured-output`).

### Số đo mở change (31/07/2026)

Bộ `followup_new_topic`, 14 kịch bản, corpus 179 tin / 535 đoạn, chạy qua `_rank` **production**
với 3 tín hiệu thật (lexical + vector Vertex + đoạn từ DB):

| cấu hình | recall@5 | recall@60 | vào ô sâu | hạng xấu nhất |
|---|---|---|---|---|
| (0) nguyên trạng | 0,786 | 1,000 | 0,643 | 29 |
| (P) + tiêu đề tin ghim, 0 gọi model | 0,786 | 1,000 | 0,786 | 26 |
| (Flex) viết lại, **không** embed lại | 0,786 | 1,000 | 0,786 | 29 |
| (F) viết lại **+ embed lại** | **1,000** | 1,000 | 0,893 | 5 |

Tự soát rò đáp án (từ có ở tiêu đề tin đích mà không suy được từ history): **3/14** ca rò, cả
ba đều đã trong top-5 ở (0) nên rò không mua gì. Bỏ hẳn ba ca đó: **0,727 → 1,000**.

Đối chiếu nhóm hồi chỉ thuần (`comparison_anaphora`, 4 ca): tiêm từ khoá recall@5 **0,000**,
embed lại **1,000**. Cùng kết luận, hai bộ kịch bản độc lập.

### Ràng buộc kế thừa, không được phá

- `_rank()` là **hàm thuần** — RS harness chạy offline/miễn phí dựa vào điều này.
- RRF đọc **thứ hạng**, không đọc điểm thô; `RRF_K = 60` không liên quan `chat_index_top_k`.
- Suy giảm êm nghĩa là **trùng khít**, không phải "vẫn chạy được".
- Prompt **không chứa UUID**; đoạn xếp hạng, **insight** mới là đích của citation.

## Goals / Non-Goals

**Goals**
- Câu nối tiếp lược chủ ngữ đưa được tin đúng vào tầm đọc (top-5 / ô sâu).
- Viết lại **sai** không được đắt hơn không viết lại.
- Cổng đo thường trực cho nhóm này, chạy trong `pytest` mặc định, **0 đồng**.

**Non-Goals**
- Sửa cổng `if not terms` (change riêng — xem D5 cho phần tương tác bắt buộc).
- Ghim → ô sâu (change riêng, ưu tiên cao hơn).
- Rerank cross-encoder; đường `insight_id` (mode B / expanded).
- Nén history (đã bác bỏ có số ở `chat-history-pinning`).

## Decisions

### D1 — Bản viết lại chỉ nuôi TRUY HỒI, không bao giờ vào prompt

Chuỗi viết lại đi vào `_question_terms` + `_embed_question`. Model trả lời vẫn nhận nguyên văn.

Lý do: *"Nên chọn cái nào trong hai cái vừa phân tích?"* mang ý định **lựa chọn** mà bản độc
lập hoá sẽ san phẳng thành một câu tra cứu. Và giữ vậy thì bán kính nổ gói gọn trong `_rank` —
đúng chỗ RS harness canh được miễn phí. Nếu bản viết lại vào prompt thì mọi hồi quy của nó chỉ
`chat_answer_harness --live` mới thấy, tốn tiền và chậm.

### D2 — RRF số hạng **THỨ TƯ**, không thay vector gốc

```
hiện tại:  1/(60+r_lex) + 1/(60+r_vec) + 1/(60+r_chunk)
sau:       1/(60+r_lex) + 1/(60+r_vec) + 1/(60+r_chunk) + 1/(60+r_vec_rw)
```

Đo được: thay hẳn vector bằng một truy vấn lệch chủ đề làm `glo-fortinet` rơi **hạng 1 → 79**,
`glo-euaiact` **1 → 86**, `glo-patch-tuesday` **[1,2] → [79,166]** — recall@5 của 8 câu chuẩn
**1,000 → 0,000**. Trong khi cùng phép nhiễu đó ở tầng **lexical** không mất gì (1,000 → 1,000).

Nguyên nhân có cấu trúc: tầng lexical là nhiều token độc lập + competition ranking nên thêm
nhiễu chỉ là thêm token; tầng vector là **một điểm** trong không gian 768 chiều nên thêm nhiễu
là **dời cái điểm đó**. Cộng thêm một số hạng ⇒ viết lại sai là **một tín hiệu xấu trên bốn**,
không phải một sự thay thế. Đúng lý do repo chọn RRF ngay từ `chat-hybrid-retrieval`.

*Đã cân nhắc:* thay vector khi "tự tin" → loại, vì độ tự tin đó chính là thứ D4 chứng minh chưa
đo được. Lấy `max(cosine)` của hai vector → loại: trộn hai thang cosine là bịa hằng số, đúng
thứ RRF sinh ra để tránh.

### D3 — **Bắt buộc** embed lại; tiêm từ khoá là code chết

(Flex) — viết lại chữ nhưng giữ vector cũ — cho **0,786**, y hệt nguyên trạng; hai ca lệch nhất
(`fub-lambda-isolation` [29], `fub-robot-oss` [21]) **không nhúc nhích**. Nhóm hồi chỉ cũng vậy
(0,000).

⇒ Mọi thiết kế "0 gọi model" cho bài toán này (gộp từ khoá từ câu trước, tiêm tiêu đề tin ghim)
là **đo được bằng không**, không phải "rẻ hơn một chút". Ghi ra đây vì nó trông rất hợp lý và
đã được ba proposal trước ghi nhầm là đã tồn tại.

### D4 — Cổng: hai phương án rẻ đã **CHẾT**, nên cổng phải LỎNG chứ không CHẶT

| phương án | tỉ lệ bắn | precision | kết luận |
|---|---|---|---|
| `_ANAPHORA_TOKENS` (`chat_intent.py`) | **44,6%** | **18,9%** | chết — `tin`/`bài` là hai danh từ phổ biến nhất của domain |
| `df_min` từ khoá đặc trưng nhất | 7,2% | 16,7% | chết — `so`/`trọng`/`chọn` hiếm vì lệch **ngôn ngữ**, không vì đặc trưng chủ đề |

Không có cổng tất định nào tách được. Nhưng **D2 làm điều đó bớt quan trọng**: khi viết lại sai
chỉ tốn một phần tư trọng số, cổng không cần chính xác — nó chỉ cần chặn **chi phí**.

Cổng chọn: **viết lại khi và chỉ khi `history` không rỗng.** Một dòng, tất định, 0 gọi model,
kiểm chứng được. Lượt đầu tiên của mọi cuộc hội thoại — phần lớn lưu lượng — không trả gì.

*Đã cân nhắc:* giao cho model quyết "câu này có cần viết lại không" → loại, đó là cộng thêm một
round-trip 1,4–1,7s để tiết kiệm một round-trip 1,4–1,7s.

### D5 — Tương tác **bắt buộc** với cổng `if not terms`

Cổng hiện tại:

```python
if not terms:            # terms = _question_terms(question)
    query_vector = None
    chunk_ranks = None
```

Với *"Hai cái này khác nhau chỗ nào?"* thì `terms == []` ⇒ cổng bắn ⇒ **mọi** vector bị ném đi,
kể cả vector bản viết lại. Đã kiểm chứng: thí nghiệm "chỉ embed lại" trên ca đó cho kết quả
**y hệt nguyên trạng** — vector truyền vào bị vứt trong im lặng.

Cổng phải áp **riêng cho từng chuỗi truy vấn**: mỗi chuỗi tự gánh cổng của chính nó.

```
terms(câu hỏi gốc)  rỗng  ⇒ bỏ tín hiệu ngữ nghĩa CỦA CÂU HỎI GỐC
terms(bản viết lại) rỗng  ⇒ bỏ tín hiệu ngữ nghĩa CỦA BẢN VIẾT LẠI
cả hai rỗng               ⇒ trùng khít bản chưa có cơ chế viết lại
```

*Đã cân nhắc và LOẠI:* tính trên **hợp** của hai chuỗi. Hợp không rỗng thì cổng không bắn, nên
vector của **câu hỏi gốc** cũng được bật — mà chuỗi đó theo giả thiết là rỗng chủ đề, tức là
đúng cái nhiễu cổng sinh ra để chặn (`rank-generic` tụt recall@5 1,00 → 0,00 khi bỏ cổng). Bản
"hợp" mua được tín hiệu viết lại bằng cách bật kèm một tín hiệu rác.

Luật theo-từng-chuỗi còn giữ nguyên bất biến của requirement *Chuẩn bị ngữ cảnh chạy song song*
(*chuỗi rỗng từ khoá SHALL KHÔNG tốn một lượt sinh embedding*): câu hỏi rỗng từ khoá vẫn không
bị embed, chỉ bản viết lại được embed.

Đây **không phải** sửa bug của cổng (bug là ca "còn token nhưng rỗng chủ đề" — 3/4 câu hồi chỉ
lọt qua, vẫn để change riêng), mà là áp đúng cổng đã có cho một chuỗi thứ hai.

⚠️ Còn một quyết định phụ thuộc: **thứ hạng đoạn lấy theo chuỗi nào** khi cả hai chuỗi đều có
nội dung. Chốt ở task 3.5, phải là **một luật duy nhất**, không rẽ nhánh ngầm theo mode.

### D6 — Fixture đông lạnh **BẢN VIẾT LẠI**, không chỉ vector

Bản viết lại là output của model ⇒ nếu harness gọi model mỗi lần chạy thì mất bất biến "miễn
phí, offline, tất định, chạy trong `pytest` mặc định" của `chat-rank-stability`.

Đông lạnh chuỗi viết lại **và** vector của nó trong fixture, kèm **dòng meta dấu vân tay**
(model id + phiên bản prompt viết lại) và `load_*` **NỔ** khi lệch — cùng luật với
`chat_chunk_ranks.jsonl`. Không có nó thì đổi prompt viết lại rồi quên sinh lại fixture sẽ để
harness đo một pipeline không tồn tại, mà mọi con số vẫn trông bình thường.

### D7 — Không tính vào `MAX_DAILY_CHAT_CALLS`, nhưng **độ trễ thì có tính**

Lượt viết lại ~vài trăm token trên model rẻ hơn một bậc — cùng lý do đã áp cho
`classify_intent` và cho lượt embed. Bộ đếm đó canh budget lượt sinh ~19k token.

Nhưng **thời gian thì không miễn phí**, và đây là cái giá thật của change:

```
TTFT hiện tại (SSE, client ấm)              2,6 – 3,9 s
+ lượt viết lại  (sàn round-trip đã đo)     1,4 – 1,7 s
+ embed bản viết lại (kết nối ấm)           ~0,37 s
────────────────────────────────────────────────────────
                                            4,4 – 6,0 s   ≈ +55…70%
```

Hai lượt gọi chạy được **song song** một phần? **Không** — embed phải chờ chuỗi viết lại xong.
Nhưng chúng song song được với `list_for_chat`, và status SSE thứ nhất vẫn phát ở 0,0s.

### D8 — Suy giảm êm = **trùng khít**

Viết lại lỗi / `CHAT_QUERY_REWRITE_ENABLED=false` / `history` rỗng ⇒ **không có số hạng thứ tư**
(bỏ hẳn, không cho mượn thứ hạng khác) ⇒ thứ tự trùng khít bản ba tín hiệu. Chat không bao giờ
500 vì viết lại.

⚠️ Cho mượn `rank_vector` như tin thiếu embedding đang làm là **sai ở đây**: ở đó "mượn" nghĩa
là *tín hiệu vắng mặt đồng ý với tín hiệu đang có* cho **một tin**; ở đây vắng mặt là **cả
lượt**, và nhân đôi trọng số tầng vector sẽ cho một thứ tự KHÁC bản ba tín hiệu — đúng chế độ
"một đường xếp hạng thứ tư xuất hiện đúng lúc hệ thống đang hỏng" mà `chat-chunk-retrieval` đã
phải viết luật để tránh.

## Risks / Trade-offs

| Rủi ro | Sức nặng | Giảm nhẹ |
|---|---|---|
| **D2 chưa được đo** — RRF thứ tư có giữ được 1,000 không? | **CAO** | Việc đầu tiên sau khi land khung: đo cả ba dạng (thay / cộng / tắt). Nếu cộng làm mất phần thắng thì change **dừng**, không nới sang "thay có điều kiện". |
| Độ trễ +55…70% TTFT | CAO | Mặc định **tắt**. Bật sau khi có số trên nhóm loại B thật. |
| Viết lại lệch chủ đề | Trung bình | D2 làm nó thành 1/4 trọng số; D8 làm ca lỗi trùng khít bản cũ. |
| Fixture mốc sau khi đổi prompt viết lại | Trung bình | D6 — dấu vân tay + nổ khi lệch. |
| Nhãn `must_have` do chính tác giả change viết | Trung bình | Đã tự soát rò (3/14, đều vô hại); `label_reason` đọc được cho từng ca; số bảo thủ 0,727 → 1,000 ghi kèm. |
| Lợi ích thật có thể nhỏ hơn đo | Trung bình | Baseline **0,786** và recall@60 **1,000** — nhóm này **không** hỏng nặng; tin đúng luôn ở trong index, chỉ nằm giữa bảng. Nói rõ trong proposal thay vì bán to. |

## Migration Plan

1. Land bộ kịch bản `followup_new_topic` + baseline **trước**, khi chưa có cơ chế nào. Có giá
   trị độc lập: hiện **0/98** kịch bản mang `history`, nên không lưới nào canh đường hội thoại
   đa lượt — kể cả đường ghim của `chat-history-pinning`.
2. Dựng số hạng RRF thứ tư sau cờ `CHAT_QUERY_REWRITE_ENABLED=false`. Cờ tắt ⇒ RS baseline
   **không đổi một chữ số** (D8) — đây là điều kiện nghiệm thu của bước này.
3. Đo ba dạng ở D2. Cộng không thắng ⇒ dừng change, ghi lại kết quả âm.
4. Bật cờ, chốt lại baseline RS **kèm lý do**, chạy `chat_answer_harness --live`.

Rollback: đặt cờ `false`. Không có migration DB, không có dữ liệu cần dọn.

## Open Questions

1. **RRF thứ tư có giữ được phần thắng không?** Chưa đo — cần chính change này để đo. Đây là
   câu hỏi quyết định sống chết, không phải chi tiết.
2. **Loại B xảy ra bao nhiêu trong lưu lượng thật?** `chat_logs` không lưu `history`, nên không
   trả lời được từ dữ liệu đang có. Ảnh hưởng trực tiếp tới việc có đáng +55…70% TTFT không.
3. **Có nên gộp với change "ghim → ô sâu" không?** Cả hai chạm cùng vùng, nhưng cái kia chữa
   loại A (recall@5 **0,000**, nặng hơn) với **0 lượt gọi model**. Nghiêng về làm cái kia trước
   và đo lại loại B sau — có thể ô sâu sâu hơn làm phần thắng ở đây co lại.
