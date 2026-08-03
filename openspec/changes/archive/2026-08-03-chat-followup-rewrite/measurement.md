# Số đo — `chat-followup-rewrite`

Corpus: **179 insight** published + is_primary · **535 đoạn** thân bài · commit nền `7785e2d`.
Ngày đo: **31/07/2026**. Cấu hình: `chat_index_top_k=60` · `chat_deep_slots=3` ·
`chat_history_pin_slots=3` · `chat_thinking_budget=256`.

Mọi con số dưới đây chạy qua **`_rank` của production**, không phải một bản mô phỏng. Lý do:
`chat-chunk-retrieval` đã đo được một lỗi (cổng rỗng-từ-khoá quên tắt tầng đoạn) mà **lượt mô
phỏng ngoài `_rank` không thấy** — script tự áp cổng ở ngoài nên lỗi bị che.

Tầng vector dùng embedding **thật** qua Vertex; thứ hạng đoạn lấy **thật** từ `document_chunks`
trong DB. DB tại thời điểm đo khớp chính xác fixture: 179 insight / 535 đoạn / 179 có embedding.

---

> ## ⚠️ ĐÍNH CHÍNH 31/07/2026 — bản đo đầu của §6/§7 SAI task_type
>
> Bản đầu của §6/§7 gọi `GeminiClient.embed_one(text)` **không truyền `task_type`**, mà mặc định
> của hàm đó là `EMBED_TASK_DOCUMENT`. Production (`ChatService._embed_question`) và
> `build_fixture_chat._write_query_vectors` đều dùng **`EMBED_TASK_QUERY`**. Nghĩa là bản đầu đo
> một cặp query↔doc **lệch với pipeline thật** — đúng chế độ hỏng mà repo này cảnh báo, và nó
> **không có gì báo lỗi**: script chạy trơn, ra số trông hợp lý.
>
> | | bản SAI (DOCUMENT) | bản ĐÚNG (QUERY) |
> |---|---|---|
> | (0) recall@5 | 0,643 | **0,786** |
> | (0) recall@60 | 0,929 | **1,000** |
> | (0) hạng xấu nhất | 72 | **29** |
> | (F) recall@5 | 0,964 | **1,000** |
>
> Lộ ra vì `chat_rank_harness` — chạy trên fixture **đúng** task_type — báo nhóm mới ở
> **r@5 ≈ 0,79** thay vì 0,64. Bài học: **số đo tay ngoài harness phải đi qua cùng một đường
> với production**, không thì nó đo một hệ thống không tồn tại.
>
> §1–§5 **không** bị ảnh hưởng: chúng dùng vector đông lạnh trong `chat_query_vectors.jsonl`,
> vốn đã luôn sinh bằng `EMBED_TASK_QUERY`.
>
> Hệ quả với kết luận: chiều và cơ chế **giữ nguyên** (viết lại phải embed lại mới thắng), nhưng
> **độ lớn của vấn đề nhỏ hơn** — xem §6.1.

---

## 1. Thí nghiệm tự nhiên đã nằm sẵn trong fixture

`chat_scenarios.jsonl` chứa **4 cặp** câu hỏi có **cùng nhãn `must_have`**: một bản tường minh và
một bản hồi chỉ, mỗi bản đã có vector câu hỏi + thứ hạng đoạn đông lạnh. Bản tường minh **chính
là** output của một reformulator hoàn hảo. Không ai dựng nó cho mục đích này.

Hạng của `must_have` trên toàn corpus 179 tin (không loại `referenced_insight_ids`, tức là mô
phỏng trường hợp người dùng **chưa bấm gì**):

| cặp | tường minh | hồi chỉ | một nửa |
|---|---|---|---|
| pq | [1, 2] | [131, 152] | [1, 7] |
| eu | [1, 2] | [142, 147] | [1, 3] |
| gemma | [1, 2] | [58, 118] | — |
| lambda | [1, 2] | [58, 99] | — |
| supply | [1, 2] | — | [3, 131] |
| **recall@5** | **1,000** (n=5) | **0,000** (n=4) | **0,667** (n=3) |

> ⚠️ **1,000 ở cột tường minh là TRẦN TRÊN phi thực tế.** Câu tường minh do người gán nhãn viết
> khi **đã biết đáp án** (*"So sánh Gemma 4 12B với DiffusionGemma"* nêu thẳng tên hai tin đích).
> Một reformulator thật chỉ thấy history + câu hỏi. §6 đo lại bằng bản viết lại **không** được
> nêu tên tin đích — đó mới là con số đáng dùng để quyết định.

---

## 2. Ba tín hiệu RRF làm câu hồi chỉ **TỆ HƠN** một tín hiệu

| kịch bản | chỉ lexical | 3 tín hiệu (production) | |
|---|---|---|---|
| `cmp-pq-anaphora` | [86, 109] | [131, 152] | tệ hơn ~45 hạng |
| `cmp-eu-anaphora` | [102, 112] | [142, 147] | tệ hơn ~40 hạng |
| `cmp-lambda-anaphora` | [1, 86] | [58, 99] | **hạng 1 → 58** |
| `cmp-gemma-anaphora` | [58, 118] | [58, 118] | trùng (cổng bắn) |

Hai tầng ngữ nghĩa — thứ `chat-hybrid-retrieval` và `chat-chunk-retrieval` dựng để **cứu** recall
— đang **phá** ở nhóm câu hỏi này, vì chúng nhúng một câu không có chủ đề.

Từ khoá của các câu đó là rác đo được:

| câu hỏi | `_question_terms` | khớp | trong đó đúng |
|---|---|---|---|
| *"Trong hai tin đó thì tin nào quan trọng hơn…"* | `['trọng','hơn']` | **88/179 (49%)** | **0/2** |
| *"Nên chọn cái nào trong hai cái vừa phân tích?"* | `['chọn','phân','tích']` | 62/179 | 1/2 |
| *"So sánh hai bài vừa rồi giúp tôi"* | `['so','giúp']` | 52/179 | **0/2** |
| *"Hai cái này khác nhau chỗ nào?"* | `[]` | 0/179 | 0/2 |

Cổng `if not terms` (`chat_service.py:899`) sinh ra để chặn đúng chế độ nhiễu này. Nó **bắn 1/4
lần** — chỉ khi terms rỗng hoàn toàn; ba câu kia lọt qua vì còn sót token vô nghĩa.

> Đây là **bug độc lập**, tách thành change riêng (xem `proposal.md` § Non-goals). §3 cho thấy
> sửa nó **không** đủ để giải bài toán này.

---

## 3. Tách đóng góp — 5 cấu hình trên 4 cặp hồi chỉ

| | pq | eu | gemma | lambda | **recall@5** | **recall@60** |
|---|---|---|---|---|---|---|
| (0) nguyên trạng | [131,152] | [142,147] | [58,118] | [58,99] | **0,000** | 0,250 |
| (G) chỉ sửa cổng | [86,109] | [102,112] | [58,118] | [1,86] | 0,125 | 0,250 |
| (L) chỉ tiêm từ khoá | [44,47] | [40,46] | [18,29] | [35,68] | **0,000** | 0,875 |
| (V) chỉ embed lại | [3,5] | [7,9] | [58,118] | [1,4] | 0,500 | 0,875 |
| (F) viết lại đầy đủ | [1,2] | [1,2] | [1,2] | [1,2] | **1,000** | 1,000 |

**(G) sửa cổng không phải lời giải** — 0,125.

**(L) tiêm từ khoá đưa tin vào index nhưng không vào tầm đọc** — recall@60 lên 0,875 mà recall@5
vẫn 0,000.

**(V) cho `gemma` là NO-OP** — [58,118], y hệt (0). Vector tường minh truyền vào bị `_rank` **ném
đi** vì `terms == []` làm cổng bắn. Đây là cơ sở đo được cho requirement *"cổng áp riêng từng
chuỗi truy vấn"*: thiết kế trực giác nhất — *giữ nguyên văn câu hỏi, chỉ embed bản viết lại* —
sẽ **không làm gì** ở đúng ca tệ nhất, và không có gì báo.

### 3.1 Phương án 0-gọi-model: nối tiêu đề tin đã ghim

`TurnCitation.title` client **đã gửi sẵn** từ `chat-history-pinning`, nên phương án này miễn phí
hoàn toàn:

| | nguyên trạng | + tiêu đề ghim | vào ô sâu (top-3) |
|---|---|---|---|
| `cmp-pq-anaphora` | [131, 152] | [42, 51] | 0/2 |
| `cmp-eu-anaphora` | [142, 147] | [40, 46] | 0/2 |
| `cmp-gemma-anaphora` | [58, 118] | [13, 18] | 0/2 |
| `cmp-lambda-anaphora` | [58, 99] | [15, 47] | 0/2 |

Nhấc 131 → 42, nhưng **0/8 vào ô sâu**, recall@5 vẫn **0,000**. Mà "có mặt trong index" thì
`chat-history-pinning` **đã bảo đảm rồi** — nên với nhóm này nó không mua thêm gì.

---

## 4. Bất đối xứng rủi ro: lexical an toàn, vector phá huỷ

Tiêm chủ đề Gemma vào 8 câu hỏi chủ đề khác (mô phỏng viết lại **sai**):

| kịch bản | gốc | + nhiễu lexical | + nhiễu lexical & vector |
|---|---|---|---|
| `glo-fortinet` | [1] | [1] | **[79]** |
| `glo-k8s-cve` | [1] | [1] | [58] |
| `glo-euaiact` | [1] | [1] | [86] |
| `glo-sbom` | [1] | [1] | [50] |
| `det-squashfs` | [4] | [4] | [50] |
| `det-jubair` | [1] | [1] | [37] |
| `glo-lambda-coldstart` | [1] | [1] | [17] |
| `glo-patch-tuesday` | [1, 2] | [1, 2] | **[79, 166]** |
| **recall@5** | 1,000 | **1,000** | **0,000** |

Nguyên nhân có cấu trúc: tầng lexical là nhiều token độc lập + competition ranking ⇒ thêm nhiễu
là **thêm token**, tin đúng vẫn khớp từ hiếm của chính nó. Tầng vector là **một điểm** trong
không gian 768 chiều ⇒ thêm nhiễu là **dời cái điểm đó**.

⇒ Cơ sở cho quyết định D2: **cộng số hạng RRF thứ tư, không thay vector gốc.**

---

## 5. Hai cổng rẻ — cả hai **CHẾT**

### 5.1 Mượn `_ANAPHORA_TOKENS` của `chat_intent.py`

```
bắn 37/83 = 44,6% số câu   ·   precision 18,9% (7/37)   ·   recall 100% (7/7)
```

Chết vì `tin` và `bài` nằm trong tập token, mà đó là hai danh từ phổ biến nhất của chính domain
này. Ca bắn nhầm: `glo-typescript` (*"Có **bài** nào về TypeScript không?"*), `glo-deepseek`
(*"DeepSeek có **tin** gì mới?"*), `glo-sbom` (*"…vì sao không thể ship thiếu **nó**?"*).

Recall 100% nên dùng được làm **tiền lọc**, nhưng tầng sau phải rẻ — mà nếu tầng sau là model thì
đã mất hết điểm.

### 5.2 Giả thuyết "độ đặc trưng từ khoá" — **SAI**

Giả thuyết: câu hồi chỉ không phải "chứa đại từ" mà là "mọi từ khoá đều phổ biến". Đo bằng
document frequency của từ đặc trưng nhất (`df_min`):

| ngưỡng `df_min ≥` | bắn | bắt được câu hồi chỉ | precision |
|---|---|---|---|
| 20 | 6/83 | 1/4 | 16,7% |
| 100 | 4/83 | 1/4 | 25,0% |
| 179 | 3/83 | 1/4 | 33,3% |

Chỉ `cmp-gemma-anaphora` (terms rỗng) tách ra. Ba câu kia có `so` (df=8), `trọng` (df=11), `chọn`
(df=21) — **hiếm trong corpus**, nhưng hiếm vì corpus tiếng Anh còn câu hỏi tiếng Việt, không
phải vì đặc trưng chủ đề. `df` thấp ở đây là **artifact ngôn ngữ**.

Đối chiếu: `squashfs` df=0 · `fortinet` df=1 · `kubernetes` df=7 · `tin` df=19 · `hơn` df=83.

> Ghi lại giả thuyết chết này vì nó trông rất hợp lý và sẽ có người nghĩ lại đúng nó.

**⇒ Không có cổng tất định nào tách được.** Nhưng D2 làm điều đó bớt quan trọng: khi viết lại sai
chỉ tốn một phần trọng số, cổng không cần chính xác — nó chỉ cần chặn **chi phí**. Cổng chốt:
*viết lại khi và chỉ khi `history` không rỗng*.

---

## 6. Baseline nhóm `followup_new_topic` — 14 kịch bản

Loại B = câu nối tiếp thừa kế chủ đề nhưng cần tin **chưa từng được trích** ⇒ ghim và working set
**không với tới theo định nghĩa**. Bất biến `must_have ∩ turn1_cited = ∅` được assert khi nạp:
**14/14 đạt**.

Bản viết lại ở đây **chỉ độc lập hoá phần bị lược**, không nêu tên tin đích — khác §1.

| kịch bản | `_question_terms` của câu trần | (0) trần | (P) +ghim | (Flex) viết lại, vector cũ | (F) viết lại + embed |
|---|---|---|---|---|---|
| `fub-eu-reg` | quy/định/theo | [2] | [2] | [2] | [2] |
| `fub-k8s-deploy` | lúc/triển/khai | [1] | [1] | [1] | [1] |
| `fub-lambda-isolation` | cách/cô/lập/mạnh | **[29]** | [26] | [29] | **[4]** |
| `fub-pq-gov` | chính/phủ/mỹ/động | [1] | [1] | [1] | [1] |
| `fub-windows-other` | lỗ/hổng/khai/thác | [9, 11] | [9, 11] | [6, 7] | [1, 5] |
| `fub-gemma-speed` | bản/sinh/văn/bản | [3] | [3] | [3] | [1] |
| `fub-supply-prevent` | phòng/ngừa/việc | [4] | [3] | [3] | [2] |
| `fub-bedrock-privacy` | dữ/liệu/giữ/lại | [1] | [1] | [1] | [1] |
| `fub-copilot-sdk` | sdk/để/tự/dựng | [4] | [1] | [1] | [1] |
| `fub-cypress-agent` | ảnh/hưởng/context | [2] | [1] | [2] | [1] |
| `fub-deepseek-strategy` | chiến/lược/dài | [1] | [1] | [1] | [1] |
| `fub-s3-modernize` | cách/hiện/đại | [1] | [1] | [1] | [1] |
| `fub-sql-paging` | phân/trang | [1] | [1] | [1] | [1] |
| `fub-robot-oss` | bên/mã/nguồn/mở | **[21]** | [21] | [21] | **[1]** |

| cấu hình | recall@5 | recall@60 | vào ô sâu | hạng xấu nhất |
|---|---|---|---|---|
| (0) nguyên trạng | **0,786** | **1,000** | 0,643 | **29** |
| (P) + tiêu đề tin ghim — 0 gọi model | 0,786 | 1,000 | 0,786 | 26 |
| (Flex) viết lại, **không** embed lại | **0,786** | 1,000 | 0,786 | 29 |
| (F) viết lại **+ embed lại** | **1,000** | 1,000 | 0,893 | 5 |

### 6.1 Đọc số này cho đúng — vấn đề NHỎ HƠN nhiều so với loại A

**recall@60 = 1,000 ở nguyên trạng.** Không tin đích nào rơi khỏi index; hạng xấu nhất là **29**.
Nghĩa là ở nhóm này model **luôn** nhìn thấy tin đúng — chỉ là thấy ở giữa danh sách chứ không ở
đầu. Đây là chuyện **khác hẳn** loại A (recall@60 **0,250**, hạng tới 152), và cũng khác hẳn ca
52% của `chat-history-pinning`.

Chỉ **3/14** ca thật sự lệch (hạng > 5): `fub-lambda-isolation` [29], `fub-robot-oss` [21],
`fub-windows-other` [9,11]. Cả ba có cùng hình dạng: câu nối tiếp mô tả một **thuộc tính**
(*"cô lập mạnh hơn"*, *"bên mã nguồn mở"*, *"lỗ hổng nào khác"*) thay vì **chủ thể** — chủ thể nằm
trong history.

**(P) và (Flex) vẫn không mua được recall@5** (0,786 → 0,786), nhưng có nhích chỗ ô sâu
(0,643 → 0,786). Kết luận cơ chế ở §8 không đổi: chỉ embed lại mới đưa tin lên đầu bảng.

---

## 7. Tự soát rò đáp án

Nhãn và bản viết lại do **chính tác giả change** viết ⇒ phải kiểm. Luật: từ nào có trong tiêu đề
tin đích mà **không suy được** từ (câu hỏi trần + câu lượt 1 + tiêu đề tin đã trích) là rò.

```
3/14 rò:  fub-k8s-deploy ['ứng','dụng']   fub-cypress-agent ['window']   fub-sql-paging ['sql','thuật']
```

Cả ba đều là ca mà **(0) đã sẵn trong top-5** — rò không mua gì. Bỏ hẳn chúng, khoảng cách **rộng
ra**, tức là kết luận không dựa vào phần rò:

| 11 ca sạch | recall@5 | recall@60 | vào ô sâu | hạng xấu nhất |
|---|---|---|---|---|
| (0) nguyên trạng | 0,727 | 1,000 | 0,545 | 29 |
| (F) viết lại + embed lại | **1,000** | 1,000 | 0,864 | 5 |

---

## 8. Kết luận đo được: phần thắng nằm **trọn** ở tầng vector

| | tiêm/sửa lexical | + embed lại |
|---|---|---|
| nhóm hồi chỉ (§3, n=4) | recall@5 **0,000** | **1,000** |
| nhóm loại B (§6, n=14) | recall@5 **0,786** = baseline | **1,000** |

Hai bộ kịch bản **độc lập**, cùng một kết luận: **reformulator là can thiệp vào embedding truy
vấn, không phải vào từ khoá.** Mọi thiết kế 0-gọi-model cho bài toán này — gộp từ khoá từ câu
trước, tiêm tiêu đề tin ghim, và cụm *"gộp‑từ‑khoá tất định"* mà ba proposal đã archive tưởng là
đã tồn tại — đều **đo được là bằng không**.

Và tầng vector chính là tầng mà §4 đo được là **phá sạch khi viết lại sai**. Phần thưởng và rủi
ro nằm trong **cùng một tầng**; không tồn tại phiên bản rẻ-và-an-toàn.

### 8.1 Điều bất ngờ: loại B hỏng **nhẹ hơn** loại A

| | recall@5 | recall@60 | cơ chế nào che? |
|---|---|---|---|
| loại A — hồi chỉ thuần | 0,000 | 0,250 | ghim + working set ✓ |
| loại B — lược chủ ngữ | **0,786** | **1,000** | **không có gì** ✗ |

Ngược với giả thuyết mở đầu. Lý do có cấu trúc: câu loại B **vẫn còn từ nội dung riêng**
(`phân trang`, `sdk`, `chiến lược`) nên tầng vector còn chỗ bám; câu loại A không còn gì.

**Ca hỏng nặng nhất thì đã có cơ chế che; ca không ai che thì hỏng nhẹ nhất.** Đây là lý do
proposal xếp change này **sau** "ghim → ô sâu", chứ không phải trước.

---

## 9. Chi phí độ trễ — **dự phóng, chưa đo**

```
TTFT hiện tại (SSE, client ấm)              2,6 – 3,9 s   ← đo thật, chat-context-depth
+ lượt viết lại (sàn round-trip flash-lite) 1,4 – 1,7 s   ← đo thật, chat-intent-hybrid-filter
+ embed bản viết lại (kết nối ấm)           ~0,37 s       ← đo thật, chat-context-depth
────────────────────────────────────────────────────────
                                            4,4 – 6,0 s   ≈ +55…70%
```

Ba số hạng đều là số đã đo, nhưng **tổng thì chưa** — tasks 7.3 phải đo thật qua `/chat/stream`.

⚠️ Đo trên client **mới mỗi câu** sẽ thổi phồng ~1,3s/câu (bắt tay TLS/auth); production dùng
`get_chat_client()` singleton nên chỉ trả một lần cho cả vòng đời process.

---

## 10. Công cụ đo

Bốn script chạy trong container backend, dùng `_rank` production + fixture:

| việc | ghi chú |
|---|---|
| A/B tường minh ↔ hồi chỉ (§1, §2) | offline, 0 đồng — fixture đã có vector cho cả hai bản |
| tách 5 cấu hình (§3) | offline, 0 đồng |
| nhiễu lexical vs vector (§4), hai cổng (§5) | offline, 0 đồng |
| baseline loại B (§6, §7) | **gọi Vertex** — embed 28 chuỗi (14 câu trần + 14 bản viết lại) + truy vấn `document_chunks` |

Bộ kịch bản 14 ca và baseline thô hiện **chưa vào repo** — task 1.2 đưa chúng vào
`tests/eval/chat_scenarios.jsonl`. Cho tới lúc đó, §6 và §7 **không tái lập được** từ repo.

---

## 11. ⛔ CỔNG 4.2 — KẾT QUẢ ÂM, CHANGE DỪNG

Đo 31/07/2026 bằng **bản viết lại thật của model** (`gemini-2.5-flash-lite`, prompt v1), đông
lạnh trong fixture, chạy qua `_rank` production với cờ `--rewrite off|add|replace`.

> ⚠️ **Cơ chế đã được GỠ sau khi đo** (xem §11.3), nên lệnh trên **không còn chạy được** từ
> repo hiện tại. Đây là đánh đổi có chủ đích: giữ lại ~200 dòng code chết chỉ để tái lập một
> kết quả âm thì đắt hơn là ghi lại đủ cách dựng lại. Muốn kiểm chứng độc lập, cần dựng lại
> bốn mảnh — tất cả đều nhỏ và đã mô tả đủ ở `design.md`:
>
> | mảnh | ở đâu | nội dung |
> |---|---|---|
> | ① prompt viết lại | `app/ai/prompts.py` | *"viết lại thành truy vấn độc lập; không trả lời; chỉ dùng thông tin trong hội thoại; đã độc lập thì chép nguyên văn"* |
> | ② lượt gọi | `GeminiClient.rewrite_query()` | flash-lite · `temperature=0` · `max_output_tokens=256` · lỗi → `None` |
> | ③ số hạng thứ tư | `ChatService._rank()` | `+ 1/(60 + rank_rewrite)`; vắng cả lượt ⇒ **bỏ hẳn**, vắng một tin ⇒ mượn `rank_vector` |
> | ④ cổng | `_rank()` | cổng rỗng-từ-khoá áp **riêng từng chuỗi** — nếu không, ca `terms == []` vứt luôn vector viết lại |
>
> Bản viết lại của model cho từng kịch bản còn nguyên trong bảng §11.2 và trong lịch sử git
> của change này.

| cấu hình | recall@5 nhóm loại B | recall@60 | vào ô sâu | TỔNG recall@5 |
|---|---|---|---|---|
| `off` — mặc định hiện tại | **0,79** | 1,000 | 0,643 | 0,881 |
| `add` — **phương án đề xuất (D2)** | **0,71** ▼ | 1,000 | 0,714 | 0,870 ▼ |
| `replace` — mốc đối chứng | 0,79 = | 1,000 | 0,714 | 0,881 = |

**Phương án đề xuất làm recall@5 TỆ ĐI.** DoD của task 4.2 viết: *"Nếu (b) không kéo recall@5
lên rõ so với (a) ⇒ DỪNG change, ghi kết quả âm, không đi tiếp."* ⇒ **dừng.**

### 11.1 Cơ chế CÓ chạy — nó chỉ không đủ

Thứ hạng đổi đúng hướng ở phần lớn ca, nên đây không phải lỗi cài đặt:

| kịch bản | off | add | |
|---|---|---|---|
| `fub-lambda-isolation` | 29 | **9** | ▲ 20 hạng |
| `fub-robot-oss` | 21 | **11** | ▲ 10 hạng |
| `fub-windows-other` | 11 | **9** | ▲ |
| `fub-copilot-sdk` | 4 | **1** | ▲ |
| `fub-cypress-agent` | 2 | **1** | ▲ |
| `fub-supply-prevent` | 4 | **6** | ▼ **văng khỏi top-5** |

Hai ca lệch nhất được nhấc 20 và 10 hạng — nhưng từ 29 lên 9 thì **vẫn ngoài top-5**, không
đổi được điểm. Còn ca duy nhất tụt lại đúng ca đang ở sát mép (hạng 4 → 6). Tổng đại số: −0,08.

Đây là hệ quả trực tiếp của §6.1 mà lúc đó chưa ai nối lại: baseline recall@60 = **1,000**
nghĩa là tin đúng **đã luôn nằm trong index**; vấn đề duy nhất còn lại là *thứ tự trong top-5*.
Mà một số hạng RRF thứ tư trên bốn thì quá **tù** để dịch chuyển mép top-5 — nó dịch được cả
vùng giữa bảng (29 → 9) nhưng không chen nổi vào ba–năm hạng đầu, nơi ba tín hiệu kia đã đồng
thuận.

### 11.2 Vì sao §6 (bản tay) hứa 1,000 mà bản thật cho 0,79

| | bản viết lại |
|---|---|
| tay (§6) | *"AWS Lambda có tuỳ chọn nào **cô lập ở mức máy ảo** không?"* |
| model | *"Cách nào cô lập mạnh hơn cho Lambda chạy Java"* |

Bản tay của tôi được viết khi **đã biết tin đích** (*"VM-level isolation"* nằm trong tiêu đề).
Phần tự soát rò ở §7 bắt được 3/14 ca rò, nhưng **không bắt được ca này** — luật soát chỉ so
từ-với-từ trên tiêu đề, mà *"máy ảo"* ↔ *"VM-level"* là rò **ngữ nghĩa**, không phải rò từ vựng.

⇒ §6 phải đọc là **trần trên của một reformulator lý tưởng**, cùng loại cảnh báo đã ghi cho §1.
Bản thật, viết đúng luật (chỉ dùng thông tin trong hội thoại), không với tới trần đó.

### 11.3 Cái gì giữ lại, cái gì dừng

**GIỮ** — có giá trị độc lập với cơ chế, đã land và xanh:

- **Bộ kịch bản `followup_new_topic`** (14 ca) + trường `turn1_question`/`turn1_cited` trong
  schema kịch bản + bất biến `must_have ∩ turn1_cited = ∅` **nổ khi vi phạm** (đã thử làm bẩn
  một nhãn → đỏ kèm thông báo đọc được). Trước đó **0/98** kịch bản mang `history`.
- **`_history_for()` trong `chat_answer_harness`.** Đây là phần thu được ngoài dự kiến:
  `_run_one` vốn truyền `history=[]` cho **mọi** kịch bản, nên khoảng trống *"0/98 kịch bản
  mang history"* mà revision 29/07 của bộ đo đó ghi lại **vừa là hạn chế của bộ kịch bản, vừa
  là hạn chế của chính runner** — và không ai nhận ra vế thứ hai. Nay bộ đo chạy được hội
  thoại đa lượt thật, tức là đường ghim của `chat-history-pinning` lần đầu có lưới thường trực.
- Hai baseline (RS + answer-eval) chốt lại kèm lý do; 0/83 kịch bản cũ đổi điểm.

**GỠ** — nhóm 3 và 5 của `tasks.md`, quyết định 31/07/2026:

| gỡ | file |
|---|---|
| `chat_query_rewrite_enabled` · `chat_query_rewrite_model_id` | `app/config.py` |
| `QUERY_REWRITE_PROMPT` · `rewrite_query()` | `app/ai/gemini_client.py` |
| tham số + số hạng thứ tư trong `_rank`, cổng-theo-chuỗi, `_rewrite_block`, nhánh gather | `app/services/chat_service.py` |
| `load_query_rewrites` · `_write_query_rewrites` · cờ `--rewrite` · `chat_query_rewrites.jsonl` | `tests/eval/` |

Lý do gỡ thay vì để sau cờ tắt: cờ mặc định `False` khiến toàn bộ khối thành **code chết** —
không có test nào chạy qua nó trong đường mặc định, nên nó sẽ mục lặng lẽ. Repo này đã có tiền
lệ đúng cho tình huống ấy (`_CAPABILITY_PHRASES`: 14/17 cụm là code chết vì một cổng chạy
trước, phát hiện sau nhiều tháng). Kết luận âm được giữ **bằng số đo**, không phải bằng code.

**KHÔNG được làm** — DoD cấm rõ: nới sang *"thay vector khi tự tin"*. `replace` không hề tốt
hơn `off` (0,79 = 0,79) mà lại mang đúng rủi ro §4 đã đo (hạng 1 → 79). Nó không phải một
phương án dự phòng, nó là phương án đã bị loại **hai lần**.

### 11.4 Điều này nói gì về hướng đi

`add` nhấc được **vùng giữa bảng** (29 → 9) nhưng không chen được vào top-5. Đó đúng là hồ sơ
năng lực của một **reranker**: RRF là phép trộn thô, còn việc phân định 5 hạng đầu cần một tín
hiệu mạnh hơn thứ hạng. Ghi nhận cho `C1. Reranking` trong
`docs/ignored/chatbot_tobe_conformance.md` — và lưu ý mốc đo bây giờ đã có sẵn.

---

## 12. Điều **CHƯA** đo

**Số hạng RRF thứ tư có giữ được 1,000 không?** Toàn bộ §3/§6 đo cấu hình **thay** vector (đưa
vector viết lại vào chỗ vector câu hỏi), vì đó là thứ đo được mà không sửa code sản phẩm. Cấu
hình mà change thật sự đề xuất — **cộng** thêm một số hạng, giữ vector gốc — **chưa có số nào**.

Không mô phỏng ngoài `_rank` được: nó cần `_rank` nhận hai vector, tức là sửa code. Và mô phỏng
RRF ở ngoài chính là chế độ hỏng mà `chat-chunk-retrieval` đã vấp.

⇒ Task 4.2 là cổng: đo cả ba dạng (tắt / cộng / thay). **Cộng không thắng ⇒ dừng change**, ghi
kết quả âm vào file này. **KHÔNG** nới sang "thay khi tự tin" — §4 đã đo cái giá là hạng 1 → 79.

Hai câu hỏi mở còn lại:

- **Loại B xảy ra bao nhiêu trong lưu lượng thật?** `chat_logs` không lưu `history` ⇒ không trả
  lời được từ dữ liệu đang có. Ảnh hưởng trực tiếp tới việc có đáng +55…70% TTFT không.
- **Ô sâu sâu hơn có làm phần thắng ở đây co lại không?** Nếu change "ghim → ô sâu" land trước,
  baseline §6 phải đo lại trước khi quyết.
