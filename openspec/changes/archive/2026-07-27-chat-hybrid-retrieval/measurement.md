# Đo lường — chat-hybrid-retrieval (27/07/2026)

Cổng bắt buộc của change này là **RS harness** (design D7): ⑥ sửa `_rank`, và RS là thứ duy
nhất bắt được hồi quy xếp hạng. Quy trình đã chạy: đo trước → áp hybrid → đo lại → chốt lại
baseline kèm lý do.

## 0. Xác minh embedding trước khi cố định schema (task 0.1)

`google-genai==0.8.0` **có** `client.models.embed_content` với
`EmbedContentConfig(task_type=..., output_dimensionality=..., auto_truncate=...)`. Không phải
tìm đường gọi thay thế.

| phép đo | kết quả |
|---|---|
| `text-multilingual-embedding-002`, chuỗi tiếng Việt | **768 chiều**, `token_count=30` |
| lô nhiều chuỗi trong một lượt gọi | được (dùng cho backfill, `EMBED_BATCH_SIZE=32`) |
| cos("cắt giảm nhân sự mảng AI" ↔ "Google layoffs hit AI division") | **0,681** |
| cos(cùng câu hỏi ↔ "Hướng dẫn cài đặt Postgres") | **0,506** |

Cặp cuối chính là chế độ hỏng change này chữa: hai cách diễn đạt khác ngôn ngữ, 0 từ khoá
chung, vẫn cách tin lạc đề một khoảng rõ ràng.

## 1. Hạ tầng (task 1.1)

`pgvector/pgvector:pg16` → pgvector **0,8,5**, có **cả `hnsw` và `ivfflat`** ⇒ Open Question
chốt **HNSW**. Volume `pgdata` cũ dùng tiếp được (cùng layout PG16), 179 insight còn nguyên.

⚠️ Image cũ là `postgres:16-alpine` (**musl**), image mới là Debian (**glibc**), mà DB tạo với
`en_US.utf8` và `datcollversion` NULL. Hai libc sắp xếp chuỗi khác nhau ⇒ đã chạy
`REINDEX DATABASE ai_radar` sau khi đổi. Ai dựng lại môi trường từ volume alpine cũ phải làm
y hệt; dựng mới hoàn toàn thì không cần.

## 2. RS harness — trước/sau (task 5.1)

**Đọc cho đúng**: bộ kịch bản vừa thêm 2 ca nhóm `semantic` (40 → 42 câu), nên số tổng KHÔNG
so được với baseline cũ. So sánh hợp lệ là **cùng 42 câu**, cột "trước" đo bằng
`--lexical-only` (tắt tầng vector ở cả hai phía) trong cùng một lượt chạy.

| | recall@60 | recall@5 |
|---|---|---|
| trước (lexical thuần, 42 câu) | 0,964 | 0,780 |
| **sau (RRF vector + lexical)** | **0,970** | **0,859** |
| baseline cũ (40 câu, không so được) | 0,988 | 0,812 |

**Không câu nào tụt.** Thắng rõ nhất ở recall@5 — thước đo nhạy, vì `CHAT_SYSTEM_PROMPT` chỉ
cho model dùng tối đa 5 tin:

| kịch bản | recall@5 | hạng xấu nhất |
|---|---|---|
| `rank-devops-trap` ("DevOps cần chú ý gì") | 0,00 → **1,00** | 47 → **1** |
| `glo-supply-chain` | 0,00 → **1,00** | 7 → 3 |
| `rank-device-trap` | 0,50 → **1,00** | 6 → 4 |
| `exp-nettacker-to-vnpost` | 0,50 → **1,00** | 9 → 2 |
| `rank-open-source-models` | 0,00 → **0,33** | 54 → 32 |
| `rank-vram-semantic` (mới) | recall@60 0,50 → **0,75** | 125 → 95 |

`rank-devops-trap` là ca minh hoạ sạch nhất: tin đúng là một checklist triển khai Kubernetes
**không hề chứa chữ "DevOps"**. Lexical thuần đẩy nó xuống hạng 47; vector đưa lên hạng 1.

Báo cáo đầy đủ per‑câu: `eval/rs_before.txt`, `eval/rs_after.txt`.

## 3. Hai điều chỉnh mà chính bộ đo ép ra

Không cái nào có trong design ban đầu — cả hai đều do đo mà lộ ra.

### 3.1 Câu hỏi rỗng từ khoá phải TẮT tầng vector

Bản đầu để vector chạy cho mọi câu. `rank-generic` ("Có gì mới không?") tụt recall@5 từ
**1,00 xuống 0,00**: tin CISA ra lệnh vá khẩn rơi xuống **hạng 23**, nhường chỗ cho những tin
có embedding tình cờ gần một câu hỏi không mang chủ đề nào. Câu rỗng nghĩa thì embedding của
nó là **nhiễu**, và nhiễu đó **đè** tầng độ quan trọng.

Cổng: `if not _question_terms(question): query_vector = None`. Điều kiện là **câu hỏi rỗng từ
khoá**, KHÔNG phải "không tin nào khớp từ khoá" — câu tiếng Việt hỏi corpus tiếng Anh cho
`_relevance = 0` ở mọi tin nhưng vẫn có nội dung ngữ nghĩa thật, và đó đúng là ca tầng vector
sinh ra để cứu.

### 3.2 Tin thiếu embedding phải MƯỢN thứ hạng lexical, không phải mất một số hạng RRF

Bản đầu: không có vector ⇒ chỉ cộng số hạng lexical. Hình phạt ngầm và rất nặng — tin thiếu
vector chỉ được **một nửa** số điểm, nên thua cả khi khớp từ khoá chính xác. Test bắt được:
tin khớp `kubernetes` nhưng chưa embed thua một tin lạc đề đã embed. Trong cửa sổ backfill
(nhiều tin NULL) đó là thiên lệch hệ thống và im lặng.

Nay tin thiếu vector mượn chính thứ hạng lexical của nó cho số hạng thứ hai ("thiếu thông tin
thì giả định tín hiệu vắng mặt đồng ý với tín hiệu đang có"). Cho cosine = 0 thì sai theo
hướng khác: 0 là một thứ hạng THẬT ở cuối bảng, tức biến "chưa biết" thành "chắc chắn không
liên quan".

## 4. Giới hạn đã đo — ⑥ KHÔNG chữa được hết

`rank-eol-khai-tu` ("Công nghệ nào sắp bị khai tử?") **đứng yên ở recall@60 0,50**:
Windows Server EOL hạng 68 → 67, còn Cypress/Electron **tụt** 19 → 53.
`text-multilingual-embedding-002` đặt top‑5 của câu này vào nhóm bài *post-quantum migration* —
nó bắt được sắc thái "phải chuyển đổi" nhưng không nối được thành ngữ **"khai tử"** với
**"end of support"**.

Kịch bản này **giữ lại trong bộ đo dù đỏ**: nó là mốc cho bước tiếp theo (rerank
cross-encoder, hoặc bảng đồng nghĩa). **Đừng chữa bằng cách sửa câu hỏi cho gần chữ trong tin
hơn** — làm thế là xoá phép đo chứ không phải cải thiện hệ thống.

Tương tự, `rank-vram-semantic` ban đầu bị gán nhãn **sai** (chỉ ExTernD là `must_have`). Đo
xong mới thấy corpus có bốn tin cùng trả lời "giảm bộ nhớ mô hình cần" — AirLLM, VKUE,
VarRate, ExTernD — và ba trong bốn nằm ngoài top‑5 của lexical. Đã sửa **nhãn**, không sửa
ngưỡng (đúng luật của `chat-eval-quality-gate`).

## 5. Chi phí

| | trước | sau |
|---|---|---|
| lượt gọi/insight lúc publish | 2 (gate + analyze) | 2 + **1 lượt embed** |
| lượt gọi/câu hỏi chat | 1–2 (sinh văn bản) | 1–2 + **1 lượt embed** |
| backfill một lần | — | 179 tin / **6 lượt gọi** (lô 32) |

Lượt embed **không** tính vào `MAX_DAILY_CHAT_CALLS` cũng như `MAX_DAILY_ANALYSIS`: hai bộ đếm
đó canh budget của lượt sinh văn bản (~19k token trên `gemini-2.5-flash`). Một lượt embed là
~30–200 token trên model embedding, rẻ hơn vài bậc — trộn chung là để lượt gọi rẻ bào mòn
budget đắt (đúng bẫy "đơn vị budget khác nhau" của repo).

Cái giá còn lại là băng thông: mỗi câu hỏi toàn cục kéo thêm ~550KB vector từ Postgres
(179 × 768 × 4 byte). Không đáng kể so với 5–22s chờ model, nhưng sẽ là lý do đẩy phần lọc thô
xuống index HNSW khi corpus tới hàng chục nghìn tin.
