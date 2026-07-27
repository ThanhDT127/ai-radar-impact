# Đo lường — chat-latency-thinking-budget (27/07/2026)

Toàn bộ số dưới đây đo trên **cùng một máy**, cùng đường mạng tới Vertex `us-central1`, corpus
179 tin. Con số **tuyệt đối** không hứa cho môi trường khác; thứ có nghĩa là **so sánh
trước/sau**.

## 1. Chẩn đoán: độ trễ đến từ đâu

Bóc từng phần của một câu hỏi toàn cục:

| thành phần | thời gian |
|---|---|
| embed câu hỏi (round-trip Vertex) | 1.303 / **1.479** / 1.762 ms (min/tb/max, n=5) |
| nạp 179 tin từ DB | 148 / **185** / 311 ms |
| `_rank` lexical thuần | 20,6 / **22,5** ms |
| `_rank` lai (RRF) | 29,3 / **32,4** ms |
| **lượt gọi model** | **phần còn lại — 9s đến 27s** |

Retrieval chiếm ~1,7s; **~90% độ trễ nằm ở lượt gọi model.**

## 2. Nguyên nhân thật: thinking tokens

| câu hỏi | thời gian | token vào | token **ra** | token **thinking** |
|---|---|---|---|---|
| "lỗ hổng nào cần vá gấp" | 14,9s | 6.537 | 233 | **2.752** |
| "mô hình mã nguồn mở nào mới" | 17,7s | 6.884 | 269 | **2.733** |
| "tuần này có tin gì quan trọng" | 14,6s | 6.699 | 282 | **1.877** |
| **prompt tầm thường** ("trả lời đúng một từ") | **10,3s** | **534** | **10** | **1.416** |

Dòng cuối là bằng chứng quyết định: **độ trễ không tỉ lệ với kích thước ngữ cảnh**. Model nghĩ
gấp ~10 lần lượng chữ nó viết ra.

### Vì sao chi phí này ẩn được 5 ngày

`google-genai==0.8.0` trả `thoughts_token_count` **rỗng**. Nhìn `usage_metadata` thì thấy
thinking = 0. Chỉ phát hiện được vì `total_token_count` (1.960) lệch so với
`prompt + candidates` (544) — phần lệch 1.416 chính là thinking. Từ SDK 1.75.0 trường này có
giá trị thật và **khớp đúng** hiệu ba số đó (đã đối chiếu).

### Vì sao KHÔNG cắt `CHAT_INDEX_TOP_K` (non-goal)

| K | thời gian | token vào |
|---|---|---|
| 60 | 17,4s | 6.537 |
| 20 | 14,2s | 2.518 |
| 10 | 11,6s | 1.540 |

Giảm **76%** token vào chỉ mua được **33%** thời gian — và trả bằng recall. Sai đường.

## 3. Chọn mức budget

Đo trên **đúng prompt chat thật** (~6,5k token vào):

| cấu hình | thời gian gọi model | thinking | chất lượng câu trả lời |
|---|---|---|---|
| không ghìm (hiện tại) | 8,2s | 1.023 | 5 marker, đúng |
| `thinking_budget=1024` | 7,8s | 892 | đúng |
| **`thinking_budget=256`** | **3,7s** | 253 | đúng — nêu đủ HiveLegacy 0-day, CISA/Fortinet |
| `thinking_budget=0` | 1,8s | 0 | đúng |

Chốt **256** (Hung quyết): 0 nhanh hơn 1,9s nhưng bỏ sạch biên suy luận, mà câu tổng hợp nhiều
tin là đúng loại câu cần nó nhất — và ngân sách 8s cho nhóm đó thì không cần ép tới 0.

## 4. Kết quả đầu-cuối (3 lần chạy mỗi câu)

| câu hỏi | lần 1 | lần 2 | lần 3 | **trung vị** | thinking |
|---|---|---|---|---|---|
| "lỗ hổng nào cần vá gấp" | 5,8s | 3,3s | 3,6s | **3,6s** | 231 |
| "mô hình mã nguồn mở nào mới" | 4,8s | 3,8s | 3,6s | **3,8s** | 253 |
| "Kubernetes có vấn đề bảo mật gì" | 3,7s | 3,2s | 3,2s | **3,2s** | 216 |
| "tuần này có tin gì quan trọng" (tổng hợp) | 3,5s | 3,6s | 4,9s | **3,6s** | 246 |

**Trước: 14,6 – 29,1s. Sau: trung vị 3,2 – 3,8s.**

⚠️ **Nhưng 4 câu là mẫu quá nhỏ và đo vào lúc mạng rảnh.** Mẫu đáng tin hơn là **62 kịch bản**
của `chat_answer_harness --live` — chạy liên tục, đủ loại câu, qua đúng pipeline thật:

| | n | trung vị | max |
|---|---|---|---|
| **1 lượt gọi model** (mode B + toàn cục) | 51 | **4,7s** | 9,5s |
| **2 lượt gọi model** (mở rộng tự động) | 13 | **6,9s** | 7,7s |
| tất cả | 62 | 5,1s (p75 6,2s · p90 7,0s) | 9,5s |

Đối chiếu mục tiêu:

- **Câu thường ≤ 5s**: trung vị **4,7s** — đạt, nhưng đuôi phân bố còn vượt.
- **Câu tổng hợp ≤ 8s**: mở rộng tự động trung vị **6,9s**, max 7,7s — đạt.
- **Còn 2/62 câu vượt 8s**: "Tóm tắt giúp mình những tin quan trọng nhất hiện có" (**9,5s**) và
  "Chuyển đổi mã hoá hậu lượng tử có hạn chót pháp lý nào" (8,8s). Cả hai đều là **1 lượt gọi**
  — tức không phải do mở rộng, mà do chính câu đó khiến model sinh dài hơn. Đây là phần chưa
  đạt, nói thẳng chứ không làm tròn xuống.

⚠️ **Phân tán còn đáng kể** (cùng một câu: 3,2s → 5,8s). Nguồn là round-trip mạng, không phải
pipeline: riêng lượt embed đã dao động 1,30–1,76s. Phải đọc **trung vị**; một lần bấm thấy 5,8s
không phải là hồi quy.

**Dư địa còn lại nếu cần ép tiếp** (chưa làm, không thuộc change này): lượt embed 1,4s hiện
chiếm ~30% ngân sách của một câu 4,7s — đó là mục tiêu lớn nhất còn lại, và nó là **sàn mạng**
chứ không phải tính toán, nên phải chữa bằng cache/bỏ bớt lượt gọi chứ không bằng chọn model
nhỏ hơn (bài học đã ghi ở `chat-intent-hybrid-filter`). Hạ `chat_thinking_budget` 256 → 0 mua
thêm ~1,9s nhưng bỏ sạch biên suy luận.

## 5. Chi phí

Thinking bị tính tiền **như output** ($2,50/1M), nên ghìm budget vừa nhanh hơn vừa rẻ hơn:

| | trước | sau |
|---|---|---|
| token thinking/câu | 1.877 – 2.752 | **216 – 253** |
| ⇒ tiền phần thinking | $0,0047 – $0,0069 | **$0,0005 – $0,0006** |

Giảm ~**tám lần** phần đắt nhất của mỗi câu trả lời.

## 6. Chệch so với kế hoạch: SDK 1.75.0 chứ không phải 2.x

Proposal viết "nâng lên 2.x". Làm tới nơi mới lộ: `google-genai>=2.0` đòi `pydantic>=2.12.5`,
đá nhau với `pydantic==2.9.2` đang pin (`pip` báo `ResolutionImpossible`). **1.75.0** là bản
cuối nhánh 1.x, chỉ đòi `pydantic>=2.9.0`, và **đã có đủ** `ThinkingConfig(thinking_budget=...)`
lẫn `thoughts_token_count` — tức là lên 2.x không mua thêm gì cho mục tiêu này mà kéo theo nâng
cả pydantic/FastAPI. Đã kiểm: SDK 1.75.0 chạy trên đúng `pydantic 2.9.2`.

## 7. Xuất xứ số của change TRƯỚC (đọc kèm)

Baseline answer-eval của `chat-hybrid-retrieval` (commit ngay trước) được **sinh lại** lúc tách
commit: lượt `--live` gốc của nó đã bị lượt của change này ghi đè trước khi kịp commit. Bản sinh
lại chạy trên `google-genai` 1.75.0 với `thinking_budget` KHÔNG đặt — hành vi tương đương bản
0.8.0 mà commit đó pin. Kết quả lệch nhẹ so với lần đo gốc (Faith 0,990 · AnsRel 0,930 → sinh lại
0,980 · 0,910); chênh lệch đó là **nhiễu judge giữa hai lượt**, không phải hồi quy do hybrid.

Hệ quả cho bảng ở mục dưới: cột "trước" của change này là **0,980 / 0,910** (số sinh lại), không
phải 0,990 / 0,930 như ghi trong lần đo đầu.

## 8. Cổng chất lượng

- **RS harness**: recall@60 **0,970**, recall@5 **0,859** — **y hệt** baseline. Đúng như phải
  thế: change này không đụng `_rank`. RS đổi số ở đây sẽ là dấu hiệu chạm nhầm chỗ.
- **`chat_answer_harness --live`** (77 lượt gọi, toàn bộ 64 kịch bản): **Faithfulness 0,99**
  (ngưỡng ≥ 0,95 ✅) · **Citation Precision 1,00** (ngưỡng = 1,00 ✅) · Answer Relevance 0,91
  (baseline 0,93, dung sai 0,05 ⇒ trong ngưỡng) · từ chối đúng 5/5 · lệch mode 0. **PASS**,
  nên **không phải nâng budget** lên 512.
  ⚠️ AnsRel nhích xuống 0,93 → 0,91 và `must_have` 68/75 → 66/75. Trong dung sai, nhưng **cùng
  chiều** với việc cắt suy luận — đây là con số phải theo dõi nếu sau này hạ budget thêm, không
  phải nhiễu để bỏ qua. Chi tiết: `eval/answer_eval_live.txt`.
- **Suite**: 326 pass, 2 skip (313 cũ + 13 test mới).
