# Số đo — `chat-history-pinning`

Corpus: **179 insight** published + is_primary · **535 đoạn** thân bài · commit nền `7785e2d`.
Ngày đo: **29/07/2026**. Cấu hình: `chat_index_top_k=60` · `chat_deep_slots=3` ·
`chat_history_pin_slots=3` · `chat_thinking_budget=256`.

---

## 1. Vấn đề — 52% tin đã bàn rơi khỏi ngữ cảnh

`_rank` chỉ nhìn câu hỏi của lượt **hiện tại**; `history` không chạm `_rank`,
`_question_terms`, hay embedding. Nên tin vừa được trích ở lượt trước không có gì bảo đảm còn
mặt ở lượt sau.

Cách đo: 6 chủ đề × 6 chủ đề. Lấy **top-3 của `_rank`** dưới câu hỏi A làm proxy cho "tin model
đã trích ở lượt đó" (prompt dặn model ưu tiên đầu danh sách), rồi tra thứ hạng của chúng dưới
câu hỏi B.

```
A \ B           security   kubernete   open_mode   regulatio    data_eng    devtools
security           1/2/3     17/12/✗      ✗/39/✗     55/28/✗      ✗/42/✗       ✗/✗/✗
kubernetes        8/✗/47       1/2/3       ✗/✗/✗     7/40/18      4/11/✗       ✗/✗/✗
open_model        54/✗/✗      ✗/24/✗       1/2/3     ✗/11/37    23/44/28    15/18/14
regulation       14/✗/32      46/✗/✗      ✗/53/✗       1/2/3       ✗/5/✗       ✗/✗/✗
data_eng          ✗/49/✗     40/53/✗       9/✗/✗      49/✗/✗       1/2/3      40/✗/✗
devtools         ✗/13/58     38/✗/26     59/29/6      17/✗/✗      56/✗/✗       1/2/3

✗ = rơi khỏi top-60 ⇒ không còn dòng dữ liệu nào trong prompt
```

**47/90 = 52%.** Hạng tệ nhất **118/179** (*Patch Tuesday*, vừa bàn ở lượt trước, người dùng
chuyển sang hỏi Kubernetes). Đường chéo `1/2/3` xác nhận phép đo chạy đúng.

Trong khi đó `_history_block` **vẫn** đưa vào prompt dòng `[«A Record-Breaking Patch Tuesday…»]`
— model đọc được cái *tên* mà không có *nội dung* nào.

> ⚠️ Giới hạn của phép đo: top-3 là **proxy** cho tin model thật sự trích. Con số có thể lệch;
> hướng và độ lớn thì đủ rõ để quyết định.

---

## 2. Vì sao KHÔNG nén history (bác bỏ hạng mục To-Be)

| Số lượt hỏi–đáp | Tin nhắn | `history_block` | Tổng prompt | % history |
|---|---|---|---|---|
| 0 | 0 | 0 c | 43.493 c | 0,0% |
| 1 | 2 | 581 c | 44.096 c | 1,3% |
| 3 | 6 | 1.172 c | 44.687 c | 2,6% |
| **5 (đầy trần)** | **10** | **1.713 c** | **45.228 c** | **3,8%** |

Bản To-Be yêu cầu nén lượt 4–10 thành một dòng tóm tắt để "tiết kiệm cửa sổ ngữ cảnh". Phần
nén được ≈ **2%** prompt — và đo trước đó đã cho thấy **bỏ hẳn ~30% prompt không đổi TTFT**
(prefill không phải nút thắt). Nén còn tốn **+1 lượt gọi model** mỗi lượt, và **làm ca ở §1 tệ
hơn** vì vứt bớt chi tiết của đúng phần đang thiếu chỗ dựa.

⚠️ `MAX_HISTORY_TURNS = 10` là 10 **tin nhắn** = **5 lượt hỏi–đáp**, không phải 10 lượt như bản
To-Be viết.

---

## 3. Giá của việc ghim — RS harness

Ghim nằm **trong** `chat_index_top_k`, tức đẩy N tin ở **đuôi** bảng xếp hạng ra. Đo bằng
`CHAT_INDEX_TOP_K` = 60 − N:

| Chỗ ghim | K hiệu dụng | recall@K | recall@5 | Biên |
|---|---|---|---|---|
| 0 | 60 | 0,968 | 0,900 | — (baseline) |
| **3** | **57** | **0,968** | **0,900** | **3 hạng** ✅ |
| 5 | 55 | 0,968 | 0,900 | 1 hạng |
| 6 | 54 | 0,968 | 0,900 | 0 — sát vách |
| 7 | 53 | **0,954** ▼ | 0,900 | ❌ gãy |

Quét rộng hơn để tìm hình dạng của đuôi:

```
 K:      60    57    55    54  │  53    52    51    50    45    40    30    20  │  10
 r@K: 0,968 0,968 0,968 0,968  │0,954 0,954 0,954 0,954 0,954 0,954 0,954 0,954│0,918
 r@5: 0,900 0,900 0,900 0,900  │0,900 0,900 0,900 0,900 0,900 0,900 0,900 0,900│0,900
                          vách ┘
```

- Vách nằm ở **hạng 54** — đúng **một** `must_have` đứng đó.
- Hạng **21–53 rỗng** (recall phẳng 0,954 suốt).
- **`recall@5` KHÔNG đổi ở mọi mức K xuống tận 10** — ghim ở đuôi không chạm phần đầu bảng,
  tức không chạm chất lượng truy hồi mà người dùng cảm nhận.

> ⚠️ Vách hạng 54 là **một điểm dữ liệu trên corpus 179 tin**, không phải hằng số của hệ thống.
> **Luật: đổi `chat_history_pin_slots` ⇒ bắt buộc chạy lại RS harness.**

---

## 4. Hiệu quả — 52% → 0%

Đo trên `build_context` (ngữ cảnh THẬT vào prompt), vì ghim là bước **sau** xếp hạng:

| | Tin đã bàn có mặt trong ngữ cảnh | Tổng tin trong prompt |
|---|---|---|
| Trước (không ghim) | 43/90 = **48%** | 60 |
| Sau (ghim 3 chỗ) | 90/90 = **100%** | 60 |

Rơi khỏi ngữ cảnh: **52% → 0%**. Trần index **không phình** (60 cả trước lẫn sau).

---

## 5. Cổng chất lượng

### 5.1 `chat_answer_harness --live` — không hồi quy

| | Baseline 28/07 | Sau change | Ngưỡng |
|---|---|---|---|
| Faithfulness | 0,99 | **0,98** | ≥ 0,95 ✅ |
| Citation Precision | 1,00 | **1,00** | = 1,00 ✅ |
| Answer Relevance | 0,94–0,95 | **0,96** | ± 0,05 ✅ |
| Từ chối đúng | 5/5 | **5/5** | — |
| `must_have` (phụ trợ) | 112/123 | **115/123** | — |
| Lệch mode | 0/98 | **0/98** | — |

**VERDICT: PASS.** Task 6.4 (giảm 3 → 2 nếu AnsRel tụt) **không kích hoạt**.

### 5.2 ⚠️ Cổng này KHÔNG phủ được rủi ro của chính change

`chat_scenarios.jsonl` có **0/98 kịch bản mang `history`**. Nghĩa là lượt `--live` **không bao
giờ đi qua đường ghim**. Nó chứng minh *không hồi quy trên các đường cũ* (vẫn cần, vì change
sửa `build_context` và `_load_refs`), **không** chứng minh *ghim vô hại*.

`design.md` bản đầu ghi "bắt buộc `--live`" như thể nó phủ được ca này — **sai**, đã sửa.

### 5.3 Bộ đo riêng cho rủi ro ghim (hội thoại 2 lượt, endpoint thật)

| Hội thoại | Ghim | Citation lượt 2 | Trong đó là tin ghim | Kết quả |
|---|---|---|---|---|
| sec → k8s | 3 | 5 | **0** | ✅ bám chủ đề mới |
| sec → devtools | 3 | 5 | **0** | ✅ bám chủ đề mới |
| k8s → regulation | 3 | 5 | **0** | ✅ bám chủ đề mới |
| model → dataeng | 3 | 5 | **0** | ✅ bám chủ đề mới |
| sec → *quay lại* | 3 | 1 | **1** | ✅ trả lời được từ tin đã bàn |
| model → *quay lại* | 3 | 1 | **1** | ✅ trả lời được từ tin đã bàn |

- **HẠI** — câu hỏi chủ đề mới bị tin ghim kéo lạc đề: **0/4**
- **LỢI** — câu quay lại tin đã bàn trả lời được: **2/2** (trước change: không với tới được)

---

## 6. Độ trễ (SSE, client ẤM — điều kiện production)

| Mode | TTFT trước | TTFT sau | Chốt trước | Chốt sau |
|---|---|---|---|---|
| meta | — | — | 0,03 | **0,02** |
| insight | 2,14 | **2,14** | 2,89 | **2,57** |
| focused | 2,94 | **2,83** | 5,03 | **4,07** |
| global | 3,22 | **2,95** | 4,79 | **4,63** |
| expanded | 4,55 | **5,22** | 5,00 | **5,30** |

19/19 đúng mode, 0 lỗi. Chênh lệch nằm trong nhiễu giữa hai lượt đo.

Chi phí thêm của ghim: **một truy vấn theo khoá chính** (`IN (...)`, ~vài ms), và **chỉ chạy
khi history có citations**. Cố ý **không** nhét vào cụm `asyncio.gather` sẵn có — `AsyncSession`
không an toàn khi hai truy vấn chạy đồng thời; cụm đó chỉ sống được vì nhánh vector phải chờ
`_embed_question` (~0,37s) xong mới chạm DB.

> ⚠️ Mọi phép đo độ trễ chat phải làm **ấm** kết nối trước: tạo `GeminiClient()` mới mỗi câu
> thổi phồng ~1,3s/câu vì bắt tay TLS/auth. Production dùng singleton.

---

## 7. Công cụ đo

Nằm ở scratchpad của phiên, **không** commit vào repo (đúng nếp gỡ scaffolding sau khi đo):

| Script | Đo gì |
|---|---|
| `measure_history_cost.py` | §2 — history chiếm bao nhiêu prompt |
| `measure_history_drift.py` | §1 — ma trận 6×6, tỉ lệ rơi khỏi top-K |
| `measure_pinning_effect.py` | §4 — trước/sau trên `build_context` |
| `measure_pin_drift.py` | §5.3 — hội thoại 2 lượt qua endpoint thật |
| `measure_nfr.py` | §6 — độ trễ SSE theo mode |

`measure_pin_drift.py` là thứ đáng đưa vào bộ đo thường trực nhất — nó là lưới **duy nhất**
chạm đường ghim. Xem "Open Questions" trong `design.md`.

---

## 8. Bổ sung sau khi archive (29/07/2026) — sửa chính sách chọn tin ghim

### 8.1 Lỗi đo được: một lượt chen giữa xoá sạch tin trước đó

`_history_pin_ids` bản đầu duyệt ngược history và lấy **cạn từng lượt**. Nhưng một lượt trả
lời toàn cục trích tới **5 nguồn**, mà chỉ có 3 chỗ ghim:

```
Lượt 1  "Bài nào bung firmware bằng SquashFS?"   → trích 1 nguồn (X)
        hỏi tiếp NGAY → ghim = [X]                ✅
Lượt 2  "có gì cho Data Engineer?"                → trích 5 nguồn
        hỏi tiếp      → ghim = 3 nguồn của LƯỢT 2 ❌ X đứng thứ 6, văng khỏi trần
```

Nghĩa là cơ chế trên thực tế chỉ phủ được **đúng lượt liền trước**, không phải "3 tin gần nhất
của cuộc hội thoại" như §1 và spec tuyên bố.

> ⚠️ **Vì sao §4 (52% → 0%) không bắt được**: script đó truyền thẳng `da_ban[:3]` vào
> `build_context`. Nó đo **chỗ đặt** (cho 3 id này, chúng có vào ngữ cảnh không) mà **không**
> đo **cách chọn** (sau hội thoại thật, có đúng 3 id đó được chọn không). Con số 0% vẫn đúng
> cho phần cơ chế; phần chính sách thì chưa từng được đo cho tới lượt này.
>
> §5.3 (2/2 câu quay lại) cũng đo trong hội thoại **chỉ có một lượt trước** — tức trước khi
> hiện tượng đẩy-ra xảy ra.

### 8.2 Sửa: quét theo LỚP

Vòng 1 lấy nguồn **thứ nhất của mỗi lượt** (lượt mới trước), vòng 2 lấy nguồn thứ hai, v.v.

| | Trước | Sau |
|---|---|---|
| Hạng của X sau một lượt chen | **6** (văng) | **2** (được ghim) |
| Ca một lượt duy nhất (hỏi tiếp ngay) | `[a,b,c]` | `[a,b,c]` — **trùng khít** |
| RS harness | 0,968 / 0,900 | **0,968 / 0,900** |
| pytest | 388 | **390** (+2 test hồi quy) |

Cái cần nhớ là **3 CHỦ ĐỀ gần nhất**, không phải 3 dòng trích gần nhất.

**Không chạy lại `--live`**: `chat_scenarios.jsonl` có 0/98 kịch bản mang `history`, nên thay
đổi này **chứng minh được** là không ảnh hưởng output của bộ đo đó — chạy lại là tốn tiền cho
một kết quả đã biết trước.

### 8.3 Ranh giới của ghim: KHÔNG mang thân bài

Kiểm chứng trên corpus — 5 định danh chỉ-có-trong-thân-bài xuất hiện **0 lần** trong
title/signal của mọi tin:

| Định danh | Trong title/signal | Trong thân bài |
|---|---|---|
| SquashFS · HMAC · Firecracker · RabbitMQ · Jubair | **0** | 1–2 |

Nên dòng ghim (title + Ý nghĩa + vai trò/chủ đề/ngày) **không thể** là nguồn cho một chi tiết
thân bài. Muốn sâu thì tin phải vào **ô sâu**: người dùng bấm citation, hoặc xếp hạng tự kéo
lên (đo được 2/5 ca rơi vào trường hợp sau).

> ⚠️ **Đừng đo việc này bằng "câu trả lời có chứa chuỗi X không".** `history` giữ lại câu trả
> lời của các lượt trước, mà những câu đó thường đã nêu chính định danh đang hỏi — đo được
> **3/3** ca. Phép đo kiểu đó tính cả *nhớ lại từ transcript* thành *ghim có tác dụng*, nên nó
> không tách được hai thứ. Muốn tách phải dựng ca mà chi tiết cần hỏi **chưa từng** xuất hiện
> trong bất kỳ câu trả lời nào trước đó.
