# Measurement — căn cứ cho `chat-context-depth`

Đo **trước khi implement**, trên fixture `backend/tests/eval/` (corpus 179 insight, ảnh chụp 27/07/2026).
Script ở `eval/` cạnh file này — chạy được lại, không phụ thuộc DB trừ phần `--live`.

```bash
docker compose cp eval/cmp_scenarios.json  backend:/tmp/ && \
docker compose cp eval/cmp_rank_spike.py   backend:/tmp/ && \
docker compose exec -e PYTHONPATH=/app backend python /tmp/cmp_rank_spike.py   # 0đ, tất định
docker compose exec -e PYTHONPATH=/app backend python /tmp/c1_depth_spike.py   # ~$0,03, gọi model
docker compose exec -e PYTHONPATH=/app backend python /tmp/detail_spike.py     # ~$0,02, gọi model
```

⚠️ Đây là **spike**, không phải harness thường trực. Nếu change được apply, 19 kịch bản so sánh phải land
vào `tests/eval/chat_scenarios.jsonl` và chạy `build_fixture_chat` để sinh query vector — không thì
`chat_rank_harness` **nổ** thay vì lặng lẽ đo lối lexical.

---

## ① Truy hồi câu SO SÁNH — 19 kịch bản (miễn phí, tất định)

| họ | n | r@60 | r@5 | **cả hai tin lọt top‑5** |
|---|---|---|---|---|
| C1 gọi tên cả hai bài | 8 | 1,00 | 1,00 | **8/8** |
| C2 hồi chỉ thuần | 4 | 0,38 | 0,00 | **0/4** |
| C3 một vế tên, một vế hồi chỉ | 3 | 0,83 | 0,67 | 2/3 |
| C4 expanded (bài đang xem free ở [1]) | 4 | 1,00 | 0,75 | 3/4 |

**C2 hỏng theo cấu trúc, không theo chất lượng.** `_question_terms("Hai cái này khác nhau chỗ nào?")` =
`['hai','cái','khác','nhau','chỗ']` — không từ nào nói về nội dung. Hai tin đúng nằm ở hạng 8–141.

Đối chứng tắt tầng vector cho thấy đây là **nhiễu**, không phải xếp hạng kém:

| kịch bản | có vector | tắt vector |
|---|---|---|
| cmp-pq-anaphora | 141, 127 | 105, 123 |
| cmp-gemma-anaphora | 22, 8 | 66, 122 |
| cmp-lambda-anaphora | 45, 111 | 1, 87 |

Thứ hạng nhảy loạn không theo hướng nào. **Không mức tinh chỉnh retrieval nào chữa được** — thông tin
"hai bài nào" không tồn tại trong câu hỏi.

> Phát hiện phụ, đáng sửa độc lập: cổng `if not terms: query_vector = None` (`chat_service.py`) **không
> bắn** cho câu hồi chỉ, vì `hai/cái/bài/chỗ` không nằm trong `STOPWORDS`. Hệ thống đi embed một câu rỗng
> nghĩa rồi xếp hạng 179 tin theo nhiễu đó — cùng chế độ hỏng mà `rank-generic` đã đo (recall@5 1,00→0,00).

## ② Độ sâu context cho câu SO SÁNH TƯỜNG MINH — 8 câu C1, gọi model thật

Hai nhánh cùng model, cùng system prompt, cùng retrieval. Chấm bằng LLM‑judge một chỉ số:
**Comparison Adequacy** (2 = đối chiếu ≥2 chiều cụ thể · 1 = mô tả song song · 0 = thiếu một bên).

| | A — hiện trạng (index 115 tok/tin) | B — ghim 2 bài (7 field, KHÔNG raw content) |
|---|---|---|
| Comparison Adequacy | **1,25 / 2** | **2,00 / 2** (8/8 câu đạt tối đa) |
| cả hai tin được trích | 8/8 | 8/8 |
| độ dài câu trả lời | 535 ký tự | 1.316 ký tự |
| độ trễ | 5.186 ms | 5.236 ms (**+50ms**) |

**Retrieval không phải thủ phạm** — cả hai nhánh trích đủ cả hai tin. Thiếu là *thiếu thứ để nói*.

Ví dụ `So sánh Gemma 4 12B với DiffusionGemma`:

```
A ── 2 gạch đầu dòng, mô tả song song, KHÔNG một con số nào
B ── 5 chiều: mục đích · kiến trúc · tài nguyên (16GB vs 18GB VRAM) ·
     hiệu năng (gần bằng 26B vs nhanh 4× nhưng chất lượng thấp hơn) · ứng dụng
```

16GB/18GB nằm trong `why_it_matters`/`so_what` — field mà `build_index_block` không đưa vào.

**⇒ Ô sâu ở mức 7 field là đủ cho so sánh; raw content không bắt buộc cho ca này.**

## ③ Câu hỏi CHI TIẾT (sự thật chỉ có trong thân bài) — 6 câu, gọi model thật

| câu hỏi | hạng bài | toàn cục | mode B |
|---|---|---|---|
| Chunk size / overlap tối ưu cho RAG? | 1 | từ chối | ĐÚNG |
| EU AI Act liệt kê rủi ro cao ở phụ lục nào? | 1 | từ chối | ĐÚNG |
| Windows Server 2022 hết hỗ trợ mở rộng tháng nào? | 1 | từ chối | ĐÚNG |
| Camera Kasa rò rỉ qua cổng UDP nào? | 1 | từ chối | từ chối |
| Entra ID khuyến nghị xác thực chống phishing nào? | 1 | **ĐÚNG** | ĐÚNG |
| Gói npm nào bị chèn mã độc vụ AsyncAPI? | 1 | từ chối | ĐÚNG |

- **Truy hồi 6/6 hạng 1** — con số phủ từ vựng 4% (mục ④) **không** dịch thành hỏng truy hồi.
- **Bịa 0/6** — fail‑closed đứng vững.
- Ca "cổng UDP" là **nhãn sai của người đo**: `9770` là số CVE (`CVE-2026-9770`), không phải cổng. Không có
  cổng UDP nào trong bài ⇒ cả hai từ chối là **đúng**. Bỏ ca này: mode B **5/5**, toàn cục **1/5**.

Ca nặng nhất, cùng corpus · cùng model · cùng thời điểm:

```
Q: "Gói npm nào bị chèn mã độc trong vụ AsyncAPI?"
toàn cục ▶ "Không tìm thấy thông tin này trong hệ thống."
mode B   ▶ "@asyncapi/specs (6.11.2-alpha.1 và 6.11.2) [1] · @asyncapi/generator@3.3.1 [1] ·
            @asyncapi/generator-components@0.7.1 [1] · @asyncapi/generator-helpers@1.1.1 [1]"
            ← và bài đó đang đứng HẠNG 1 trong chính lượt toàn cục kia
```

Thiệt hại không phải "trả lời sai" mà là **khẳng định sai về độ phủ hệ thống** — người dùng kết luận
"radar không có tin này" rồi thôi tìm. Cùng họ với lỗi `empty_roles` từng tuyên bố sai
"hệ thống không có tin nào cho vai trò Dev".

## ④ Chi phí độ sâu (đo trên 10 bài có raw content trong fixture)

```
index 60 dòng                     ≈ 6.937 token   (115 token/tin)
build_insight_block full          1.527 – 3.466 token
   ├─ raw content                   886 – 2.628   (58–76%)
   └─ CHỈ 7 field phân tích          641 –   838
```

Phủ từ vựng của biểu diễn truy hồi so với thân bài: **4,0% (vector) / 4,1% (lexical)** trên 3.809 token
từ vựng của 10 bài. Con số này là căn cứ của change **`chat-chunk-retrieval`** (③), không phải của change
này — mục ③ ở trên cho thấy nó **không** làm hỏng truy hồi.

Ngân sách xấu nhất của thiết kế đề xuất: `3 ô sâu × 3.466 + 57 dòng index × 115 = 16,9k token`, dưới mức
~19k mà production đã chạy từ `chatbot-qa`.

## Baseline cần chốt lại sau khi apply

| bộ đo | vì sao | lệnh |
|---|---|---|
| `chat_rank_harness` | thêm 19 kịch bản so sánh ⇒ tập kịch bản đổi | `--freeze-baseline` kèm lý do |
| `chat_answer_harness --live` | sửa `CHAT_SYSTEM_PROMPT` + đổi context ⇒ đổi câu trả lời | chốt lại Faith/AnsRel/CitPrec |

Ngưỡng gate **không đổi**: Faithfulness ≥ 0,95 · Citation Precision = 1,00.

---

# SAU KHI APPLY (28/07/2026)

Cùng script, cùng fixture, chỉ khác pipeline. `A` của spike C1 giờ **là pipeline thật** (đã có
ô sâu tự động), nên cột "trước" bên dưới lấy từ số đo ở phần trên cùng tài liệu.

## ① Câu hỏi CHI TIẾT — phần ②′ (hydration tự động, 0 thao tác người dùng)

| câu hỏi | toàn cục TRƯỚC | toàn cục SAU |
|---|---|---|
| Chunk size / overlap tối ưu cho RAG? | từ chối | **ĐÚNG** |
| EU AI Act liệt kê rủi ro cao ở phụ lục nào? | từ chối | **ĐÚNG** |
| Windows Server 2022 hết hỗ trợ mở rộng tháng nào? | từ chối | **ĐÚNG** |
| Camera Kasa rò rỉ qua cổng UDP nào? | từ chối | từ chối ✅ |
| Entra ID khuyến nghị xác thực chống phishing nào? | ĐÚNG | ĐÚNG |
| Gói npm nào bị chèn mã độc vụ AsyncAPI? | từ chối | **ĐÚNG** |

**1/5 → 5/5** trên các câu trả lời được. Ca "cổng UDP" vẫn từ chối và đó là **đúng** — tiền đề
sai (`9770` là số CVE, không phải cổng). Truy hồi vẫn 6/6 hạng 1, không đổi.

## ② Câu SO SÁNH tường minh — phần ①

| | TRƯỚC (index 115 tok/tin) | SAU (3 ô sâu + index) |
|---|---|---|
| Comparison Adequacy | 1,25 / 2 | **2,00 / 2** (8/8 câu) |
| cả hai tin được trích | 8/8 | 8/8 |
| độ dài câu trả lời | 535 ký tự | 2.266 ký tự |
| **độ trễ** | 5.186 ms | **8.426 ms** |

Đối chứng "chỉ 7 field, không raw content" chạy cùng lượt cho **1,75/2** — thấp hơn bản có
raw content. Kết luận đổi so với đo lần đầu: **`chat_deep_include_content=true` là đúng**,
và nội dung bài gốc có đóng góp thật cho cả câu so sánh, không chỉ câu chi tiết.

### ⚠️ Độ trễ +62% — cái giá không có trong dự toán design

Design D2 ước "+50ms", dựa trên spike đo **2 ô sâu chỉ-7-field**. Bản thật là **3 ô sâu KÈM
raw content**, và phần lớn chi phí không nằm ở prompt mà ở **output dài gấp 4** (535 → 2.266
ký tự). Đúng theo bài học `chat-latency-thinking-budget`: độ trễ đi theo token SINH RA, không
theo token đọc vào.

Van xả nếu cần, theo thứ tự nên thử:
1. `CHAT_DEEP_INCLUDE_CONTENT=false` — về 7 field, mất phần thắng câu chi tiết (5/5 → 1/5).
2. `CHAT_DEEP_SLOTS=2` — giữ được so sánh hai tin, bớt một bài raw content.

**Đừng hạ `CHAT_INDEX_TOP_K`** — nó không phải nguồn của độ trễ này.

## ③ Benchmark xếp hạng (RS) — miễn phí, tất định

Baseline chốt lại 28/07 kèm lý do trong `BASELINE_META.revisions`. Tổng đi từ
recall@60 0,970 → **0,922** và recall@5 0,859 → **0,821**, **KHÔNG so được trực tiếp**: bộ
kịch bản đi từ 42 lên 61 câu, và nhóm mới `comparison_anaphora` **cố ý đỏ**.

| nhóm mới | n | r@60 | r@5 |
|---|---|---|---|
| `comparison` (gọi tên cả hai) | 8 | 1,00 | **1,00** |
| `comparison_expanded` | 4 | 1,00 | **1,00** |
| `comparison_partial` | 3 | 0,83 | 0,67 |
| `comparison_anaphora` | 4 | 0,25 | **0,00** ← mốc đo, không phải mục tiêu |

`comparison_anaphora` đỏ ở RS là **đúng thiết kế**: `_rank` không thể biết "hai bài nào" từ
một câu không chứa thông tin đó. Nó được chữa bằng working set, và phần đó đo ở
`chat_answer_harness` (`mode="focused"`), không ở RS.

**0 kịch bản cũ nào tụt.**

Phần `STOPWORDS` (task 6.1) đo riêng: r@5 tổng 0,805 → **0,821**, và
`comparison_expanded` r@5 0,75 → **1,00**. Đổi lại `comparison_anaphora` r@60 0,38 → 0,25 —
thứ hạng cũ là **may mắn của nhiễu**: đối chứng bật/tắt tầng vector cho thứ hạng nhảy loạn
không theo hướng nào (141↔105, 22↔66, 45↔1).


## ④ Chất lượng câu trả lời (`chat_answer_harness --live`, 83 kịch bản)

| | baseline 27/07 | sau change | ngưỡng |
|---|---|---|---|
| Faithfulness | 0,991 | **0,99** | ≥ 0,95 ✅ |
| Citation Precision | 1,000 | **1,00** | = 1,00 ✅ |
| Answer Relevance | 0,922 | **0,93** | baseline ± 0,05 ✅ |
| từ chối đúng | 5/5 | 5/5 | |
| lệch mode | 0/56 | **0/83** | |

3 kịch bản cũ tụt AnsRel (đều là judge chấm **P cho câu trả lời đúng**), **7 tăng** ⇒ net dương.

| nhóm mới | n | faith | ansrel |
|---|---|---|---|
| `comparison` | 8 | 1,00 | **1,00** |
| `comparison_anaphora` | 4 | 1,00 | 0,88 |
| `comparison_partial` | 3 | 0,92 | 1,00 |
| `comparison_expanded` | 4 | 0,96 | 0,62 ← đường legacy |

### ⚠️ Lượt đo đầu cho Faith 0,78 — hồi quy GIẢ của bộ đo

```
pipeline ──▶ 3 ô sâu: 7 field + NỘI DUNG BÀI GỐC      (model đọc cái này)
bộ đo    ──▶ _cited_context() dựng lại dòng index nén  (judge đọc cái này)
                    ▲ luật viết từ thời chỉ có MỘT tin sâu (mode B)
⇒ mọi khẳng định rút từ thân bài bị chấm N ⇒ 0,991 → 0,78, đủ để chặn merge
```

Chữa bằng `ChatContext.deep_blocks` (block **đúng như đã phục vụ**, theo số) — không suy lại
được từ corpus vì fixture chỉ lưu `normalized_content` của anchor. Khoá bằng
`test_cited_context_uses_served_depth_not_reconstructed_index`.

**Lỗi sống ở khe giữa pipeline và bộ đo** — cả hai bên đều đúng theo cách hiểu của mình.

### ⚠️ Defect thật mà bộ đo tìm ra: `_COMPARISON_RULE` làm model quên marker

Bản đầu mở đầu bằng *"ghi đè phần ĐỘ DÀI ở trên"* ⇒ model hiểu rộng thành ghi đè luôn luật
marker ⇒ viết đoạn đối chiếu văn xuôi **không có `[n]`** ⇒ `enforce_grounding` fail-closed
xoá sạch một câu trả lời đúng. Chập chờn ~25% (`cmp-gemma-anaphora` đạt 2/2 ở lượt smoke,
0/2 ở lượt full). Chữa bằng một dòng nói rõ luật **chỉ** nới độ dài/bố cục: nhóm đó
AnsRel **0,00 → 1,00**, must_have 8/8.

Không unit test nào bắt được "model đôi khi quên marker khi được phép viết dài hơn".

**Chi phí đo tổng: 3 lượt `--live` ≈ $1,5** (lượt 1 bỏ vì bộ đo hỏng, lượt 2 bỏ vì snapshot
trộn hai phiên bản prompt).


---

## ⑤ SỬA SỐ ĐỘ TRỄ (28/07/2026) — bản trên đo SAI ĐIỀU KIỆN

Con số **8.426ms** ở mục ② đo trên **đường blocking** và tạo `GeminiClient()` **mới mỗi câu**.
Production đi SSE và dùng `get_chat_client()` **singleton** (design D6). Đo lại đúng điều kiện:

```
                status   TTFT    tổng   phần streaming che
so sánh          0,0s    3,3s    7,0s        3,7s
chi tiết         0,0s    2,6s    3,1s        0,6s
câu thường       0,0s    3,0s    4,1s        1,1s
```

Phân rã một câu so sánh (3 lần liên tiếp, cùng tiến trình):

| chặng | lần 1 (lạnh) | lần 2 | lần 3 |
|---|---|---|---|
| embed câu hỏi | 1,67s | **0,37s** | **0,37s** |
| `_rank` | 0,034s | 0,035s | 0,042s |
| dựng prompt | 0,001s | 0,001s | 0,002s |
| model → token đầu | 3,53s | 2,41s | 3,09s |
| model tổng | 6,66s | 5,56s | 5,43s |

⇒ **85% TTFT là lượt gọi model.** Và con số "embed 1,4s" trong CLAUDE.md là **cold-start**,
không phải sàn mạng — đã sửa lại ở đó.

### Ba hướng tối ưu đã đo và LOẠI

| hướng | đo được | kết luận |
|---|---|---|
| cắt ngắn câu trả lời | phần dài nằm SAU token đầu | streaming đã che ⇒ đổi Adequacy lấy số vô hình |
| bỏ raw content khỏi ô sâu | TTFT 3,3 → 3,2s | trong nhiễu, mà câu hỏi chi tiết **quay lại từ chối** (44 và 122 ký tự = `INSUFFICIENT_GROUNDS_MESSAGE`) |
| hạ `chat_index_top_k` | prefill không phải nút thắt | bỏ ~30% prompt không đổi TTFT |

### Đã làm thay: status mang số liệu thật (0 đồng, không đánh đổi)

`_reading_status(ctx)` thay `STATUS_COMPOSING` chung chung ở đường `_answer_global`:

```
0,00s  "Đang tìm trong hệ thống…"
0,44s  "Đang đọc kỹ 3 tin: «Announcing Lambda MicroVMs…», «Eliminating Java cold starts…»
        và 1 tin nữa trong 61 tin khớp…"
3,3s   token đầu
```

Vẫn ĐÚNG HAI status — thêm sự kiện thứ ba cách nhau vài chục ms chỉ làm dòng chữ nhấp nháy.
Mode B giữ mốc chung vì không đi qua `build_context`. Test: 3 ca trong
`test_chat_context_depth.py` + hai assertion chuỗi status trong `test_chat_streaming.py`.


---

## ⑥ ĐO LẠI TRÊN ĐƯỜNG THẬT (28/07/2026) — sửa phép đo, không đổi code

Bốn kịch bản `comparison_expanded` mô tả payload `insight_id`+sentinel, nhưng sau change này
widget **luôn** đưa bài đang xem vào working set ⇒ nó gửi `referenced_insight_ids`. Nhãn cũ đo
một luồng đã chết. Đã chuyển sang `mode=focused` + nhóm `comparison_in_article`.

Cùng lúc sửa một chỗ RS đo sai: tin đi qua `referenced_insight_ids` vào **thẳng ô sâu**, không
qua xếp hạng — nên chấm recall `_rank` cho chúng là chấm một phép tính không tồn tại, và nó cho
`comparison_anaphora` **0,00 vĩnh viễn** ở đúng nhóm mà production trả lời hoàn hảo.

| | trước | sau |
|---|---|---|
| RS recall@60 | 0,922 | **0,969** |
| RS recall@5 | 0,821 | **0,876** |
| RS `comparison_anaphora` | 0,00 (giả) | **—** (không có việc để đo) |
| RS `comparison_in_article` | — | **1,00 / 1,00** |
| AnsRel nhóm `comparison_in_article` | 0,62 | **1,00** |
| AnsRel `cmp-gemma-expanded` | 0,00 | **1,00** |
| **TỔNG Faith** | 0,99 | **1,00** |
| **TỔNG AnsRel** | 0,93 | **0,96** |
| **TỔNG CitPrec** | 1,00 | **1,00** |

`_rank` **không đổi một dòng** — toàn bộ mức tăng đến từ việc thôi đo những thứ không tồn tại.

⚠️ **Một đại lượng đỏ mãi vì thiết kế sẽ dạy người đọc bỏ qua nó**, và nó làm trung bình tổng
bớt nhạy với hồi quy thật. Bằng chứng "xếp hạng thuần KHÔNG giải được câu hồi chỉ" vẫn nguyên ở
mục ① của tài liệu này + script trong `eval/` — chỗ đúng của nó là **tài liệu đo một lần**,
không phải một cổng chạy mãi.
