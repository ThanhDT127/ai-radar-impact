# Đo hồi quy xếp hạng cho task 4.1 (`_relevance` khớp theo biên từ)

Công cụ: `tests.eval.chat_rank_harness` (`chat-rank-stability`, land 27/07/2026).
Corpus: `chat_corpus.jsonl` — 179 insight `published` + `is_primary`, ảnh chụp 27/07/2026.
K = 60 (`chat_index_top_k`); recall@5 = trần "TỐI ĐA 5 tin" của `CHAT_SYSTEM_PROMPT`.

## Tổng

| | trước 4.1 | sau 4.1 |
|---|---|---|
| recall@60 | 1,000 | **0,988** |
| recall@5 | 0,812 | **0,812** |

## Từng câu đổi số (5/47 kịch bản)

| kịch bản | nhóm | r@60 | r@5 | hạng xấu nhất | nguyên nhân |
|---|---|---|---|---|---|
| `exp-gemma-to-eol` | deprecation | 1,00 → **0,50** | 0,50 → 0,50 | 48 → **76** | tin Cypress mất khớp `kế`, vì trước đó nó khớp **chuỗi con trong `kết`** |
| `exp-nettacker-to-vnpost` | vietnamese | 1,00 → 1,00 | 1,00 → **0,50** | 3 → 9 | `sql` không còn khớp **`MySQL`** |
| `glo-open-model-analysis` | open_model | 1,00 → 1,00 | 0,50 → **1,00** | 6 → 5 | bớt nhiễu ⇒ tin đúng nhích lên top-5 |
| `glo-patch-tuesday` | security | 1,00 → 1,00 | 0,50 → 0,50 | 6 → 37 | tin thứ hai tụt hạng nhưng vẫn ngoài top-5 ở cả hai bên |
| `rank-devops-trap` | role_trap | 1,00 → 1,00 | 0,00 → 0,00 | 47 → 60 | tụt trong vùng không ai đọc tới |

## Ba kết luận, và không cái nào là cái change này dự đoán

### 1. Lợi ích đo được trên corpus này ≈ **0**

Net recall@5 không đổi (một câu +0,50, một câu −0,50). recall@60 chỉ **giảm**. Đổi này đúng
về nguyên tắc nhưng **không cải thiện được gì đo được** ở đây.

### 2. Ví dụ chủ lực của D3 là **ca không thể xảy ra**

D3 lập luận: `"ai"` khớp nhầm trong *email, domain, training, detail*. Nhưng `ai` nằm trong
`STOPWORDS` (đại từ tiếng Việt), nên `_question_terms` **loại nó trước khi** `_relevance`
nhìn thấy. Term `ai` chưa bao giờ tới được chỗ bị cho là hỏng.

### 3. Nguồn pha loãng THẬT là **taxonomy topic**, không phải chuỗi con

Câu "Có tin nào về ML không?" → **123/179 tin** có relevance = 1, cả sau khi sửa. Lý do:
`_relevance` đọc `insight.topics`, mà hai trong 12 topic đóng là **"AI/ML Ứng dụng"** và
**"AI/ML Nghiên cứu"** — token hoá ra đúng chữ `ml`. Đó là khớp **trọn từ**, hoàn toàn hợp
lệ theo D3, nên khớp-theo-biên-từ không đụng được tới nó. Tin đúng nhất
(*Operating AI/ML Workloads on Kubernetes*) vẫn nằm hạng **54** cả trước lẫn sau.

Nhóm `ascii_short` — nhóm câu dựng ra để đo đúng thay đổi này — **không đổi một số nào**.

## Quyết định: vẫn land, và chốt lại baseline ở mức mới

- Spec delta `chat-qa-service` yêu cầu tường minh khớp theo biên từ; bản mới **đúng spec**,
  bản cũ thì không.
- Hai ca "tụt" đều đọc được và không phải hồi quy chất lượng thật:
  - `kế` → `kết` là **khớp nhầm**; tin Cypress trước nay sống nhờ tai nạn. Phần tóm tắt tiếng
    Việt của nó không hề chứa "hết/vòng/đời/hỗ/trợ", nên nó **chưa bao giờ thực sự tìm được**
    bằng cách diễn đạt đó — code cũ chỉ che chuyện đó đi.
  - `sql` ≠ `MySQL` là **mất thật**, nhưng là hệ quả trực tiếp của chính luật D3 đòi hỏi.
- Vì vậy chốt lại baseline ở mức mới (recall@60 0,988 · recall@5 0,812), **kèm lý do này**.
  Không chốt lại thì guard nằm ở mức code-còn-lỗi và một lần revert 4.1 sẽ lọt qua harness.

---

# Xác minh end-to-end trên hệ thống đang chạy (task 7.1 / 7.2)

## 7.1 — Mode A: lỗi này KHÔNG hề là giả thuyết

`POST /api/v1/chat` thật, câu hỏi *"So sánh tin về mô hình mã nguồn mở với tin về bảo mật
nghiêm trọng"*. Model phát ra dãy marker:

```
[42] [39] [2] [16] [38]
```

Đối chiếu trên chính dãy đó:

| marker | cách CŨ `citations[n-1]` | cách MỚI `find(c.n === n)` | |
|---|---|---|---|
| `[42]` | undefined | How Open Models Are Driving AI Research | ⚠️ cũ mất link |
| `[39]` | undefined | NVIDIA Nemotron | ⚠️ cũ mất link |
| `[2]` | **NVIDIA Nemotron** | CISA urges immediate action on Fortinet | ❌ **cũ TRỎ SAI TIN** |
| `[16]` | undefined | TP-Link Kasa camera | ⚠️ cũ mất link |
| `[38]` | undefined | Local AI is ready for production | ⚠️ cũ mất link |

Nghĩa là trên một câu hỏi bình thường, bản cũ **mất 4/5 link** và **1 link trỏ sang tin khác**;
danh sách nguồn thì hiện `[1][2][3][4][5]` trong khi câu văn nói `[42][39][2][16][38]`.

⚠️ **Design doc của change này nói "hiện tại nó đang đúng"** và dự đoán lỗi chỉ lộ ra khi xếp
hạng kém đi. Đo thật cho thấy **nó đã hỏng sẵn rồi**: với top-K = 60 và xếp hạng hai tầng,
model chọn tin rải khắp index nên marker nhảy cóc là **thường**, không phải hiếm.

## 7.2 — Mode B không hồi quy

`insight_id` = TP-Link Kasa, hỏi *"Lỗ hổng của camera này là gì?"* → `mode="insight"`, marker
`[1] [1] [1]`, citation duy nhất mang `n = 1`, mọi marker giải được. Đường vốn đang đúng vẫn đúng.

## 3.3 — Log marker nhảy cóc

`DEBUG app.services.chat_grounding: Marker không liền mạch từ 1: [42, 39, 2, 16, 38] (index 60 tin)`
— bắn đúng khi nhảy cóc, im lặng với dãy `[1][2][3]`.

---

## Việc còn lại (KHÔNG thuộc change này)

Recall ngữ nghĩa — `sql`↔`MySQL`, "hết vòng đời"↔"ngừng hỗ trợ", và pha loãng do topic — là
đúng phạm vi **`chat-hybrid-retrieval` (⑥)**. Đừng cố chữa bằng cách vặn thêm luật so chuỗi;
số ở trên cho thấy hướng đó đã cạn.
