# Đo: chat-chunk-retrieval

Đo 28/07/2026 trên corpus fixture `chat_corpus.jsonl` (179 insight, ảnh chụp 27/07 — cùng corpus
mọi baseline chat đang dùng). Công cụ ở `eval/`, chạy lại được.

---

## 0.1 — Bộ kịch bản "khám phá bằng chi tiết"

**Vì sao phải đào bằng máy.** Spike của `chat-context-depth` soạn 6 câu hỏi chi tiết bằng tay và
**cả 6 truy hồi đúng ở hạng 1** — vì người soạn vô thức chọn chủ đề mình nhớ được, mà thứ nhớ
được chính là thứ nằm trong tiêu đề. Muốn đo đúng chế độ hỏng thì tiêu chí chọn định danh phải
**kiểm được**, không phải trực giác.

`eval/mine_detail_terms.py` giữ một định danh làm ứng viên khi nó thoả **cả năm**:

1. xuất hiện ≥ 2 lần trong `normalized_content` của một bài;
2. vắng trong biểu diễn truy hồi của **chính bài đó** (`title/signal/so_what/summary_short/topics`
   — đúng bộ field `_relevance` soi và `build_embedding_text` embed);
3. vắng trong biểu diễn truy hồi của **mọi bài khác** (nếu có ở nơi khác, câu hỏi sẽ kéo nhầm bài
   kia lên và ca đo hoá ra đang đo chuyện khác);
4. chỉ nằm trong thân bài của **đúng một** insight ⇒ `must_have` có đúng một phần tử;
5. "trông như định danh": có chữ số / CamelCase / ACRONYM / `-` `.` `@`.

> ⚠️ **Một dương tính giả đã bị bắt và phải giữ cổng chặn nó.** Bộ đếm thân bài giữ `.`/`-`/`@`
> bên trong token, còn `_question_terms` **cắt** ở đó. Nên `v3.7.0` trông như "vắng khắp nơi",
> trong khi câu hỏi chứa nó thực ra đi vào `_relevance` thành `v3`,`7`,`0` và bài
> *Announcing etcd v3.7.0* khớp ngay ở tiêu đề. Ứng viên chỉ hợp lệ khi **mọi mảnh** của nó
> (theo regex câu hỏi) đều vắng. Không có cổng này thì bộ kịch bản chứa những ca mà tầng lexical
> đang hoạt động bình thường, và kết luận gate sẽ sai theo hướng "có vẻ hỏng nặng".

Kết quả: **141/179 bài** có ít nhất một định danh độc quyền thân bài. Chọn tay **15 ca**
(`eval/detail_scenarios.jsonl`), mỗi ca một `label_reason` nói rõ định danh nào, đếm bao nhiêu lần,
và phần phân tích nói gì thay thế.

## 0.2 — `_rank` hiện tại trên bộ đó

`eval/measure_detail_rank.py` (0 lượt gọi model khi đã có vector đông lạnh, `_NoModel` nổ nếu
`_rank` chạm model).

| | |
|---|---|
| recall@5 | **0,667** (10/15) |
| recall@60 | 1,000 |
| hạng trung vị | 1 |
| hạng xấu nhất | **29** |

Năm ca ngoài top-5 — tức **33,3%**, vừa qua cổng 30%:

| kịch bản | định danh | hạng |
|---|---|---|
| `det-spdx-cyclonedx` | SPDX / CycloneDX | 29 |
| `det-hmac-agent` | HMAC-SHA256 / AgentAuthz | 20 |
| `det-chunking-strategy` | ChunkingStrategy | 15 |
| `det-squashfs` | SquashFS | 7 |
| `det-ssrf-assumerole` | SSRF / AssumeRole | 6 |

**Đọc con số này cho đúng.** recall@60 = 1,000 nghĩa là bài đúng **luôn lọt index** — chế độ hỏng
không phải "mất hẳn bài" mà là "bài nằm ngoài 5 tin model thực sự dùng" (`CHAT_SYSTEM_PROMPT`:
TỐI ĐA 5 tin). Mười ca còn lại ở hạng 1–2 vì tầng vector mức insight **vẫn bắt được chủ đề**
(hỏi Eytzinger thì bài "static search tree" gần về ngữ nghĩa dù không có chữ Eytzinger). Đó là lý
do 33,3% chứ không phải 90%: change này chữa phần đuôi, không chữa một hệ thống mù.

⚠️ **33,3% so với cổng 30% là sát**, và bộ kịch bản do chính người viết change chọn tay từ 141 ứng
viên. Con số này **một mình không đủ** để trả cái giá kiến trúc ở mục Impact — nên có 0.3.

## 0.3 — Quyết định: **TIẾP TỤC**

Cổng của `proposal.md` (≥ 30% ngoài top-5) **đã qua ở 33,3%**. Vì mức sát, quyết định được chốt
bằng một phép đo thứ hai, **triển vọng**: `eval/simulate_chunk_signal.py` chunk + embed toàn bộ
535 đoạn của 179 bài rồi chạy **chính `ChatService._rank` thật** với `chunk_ranks` — không có bản
sao logic xếp hạng nào, vì đo một bản sao là đo một pipeline không tồn tại.

### ① Nhóm `detail_discovery` — cái change nhắm tới

| | trước | sau |
|---|---|---|
| recall@5 | 0,667 | **1,000** |
| hạng xấu nhất | 29 | **4** |

Cả **5/5** ca hỏng được chữa, không ca nào tụt: 29→4, 20→3, 15→2, 7→4, 6→3. Mười ca vốn ở hạng 1
đứng yên hoặc tốt lên (2→1 ở `det-ipfs-c2`, `det-firecracker`).

### ② 68 kịch bản RS hiện có — điều kiện KHÔNG TỤT

recall@5 trung bình **0,876 → 0,874**: 3 câu tốt lên, 3 câu tụt. Đây là **phẳng**, không phải một
phần thắng.

Ba câu tụt, xem kỹ từng ca — **cả ba giữ nguyên `must_have` chính ở hạng 1**, cái rơi là tin thứ
hai của một câu hỏi rộng:

| câu | tin tụt | hạng |
|---|---|---|
| `glo-iot-security` "Thiết bị IoT có sự cố bảo mật nào không?" | Popa Botnet | 3 → 6 |
| `rank-device-trap` "tin về device IoT mới" | bowling center DIY | 4 → 18 |
| `cmp-pq-partial` | CISO guide to post-quantum | 2 → 7 |

Chỗ chúng nhường lại cho tin **cùng chủ đề, khớp sâu hơn ở thân bài** (CISA vá khẩn, Secure Boot,
Patch Tuesday cho câu IoT-bảo-mật). Tức là đây là **đổi thứ tự trong cùng một vùng liên quan**,
không phải tin đúng bị đẩy ra ngoài — khác hẳn chế độ hỏng recall thật mà RS harness sinh ra để
bắt. Ba câu tốt lên đối trọng: `glo-patch-tuesday` 0,50→1,00, `rank-open-source-models`
0,33→0,67, `cmp-supply-partial` 0,00→0,50.

**Kết luận có số**: bỏ ra một bảng + 535 vector (≈ 3× số hàng vector hiện có) để đổi lấy
recall@5 nhóm mục tiêu **+0,333 tuyệt đối (5/5 ca hỏng)** trong khi phần còn lại đứng yên
(−0,002, trong nhiễu). **Tiếp tục.**

### Số vận hành đo được luôn ở lượt này

| | |
|---|---|
| số đoạn / 179 bài | **535** (trung bình 3,0 đoạn/bài; trần D3 là ≤6 — đúng) |
| thời gian embed cả corpus | **39,1s** (một lượt `embed()` gộp lô) |
| dung lượng vector đoạn | 4,3MB JSONL ⇒ ~1,6MB trong Postgres (535×768×4 byte) |

535 đoạn chứ không phải ~1.000 như `proposal.md` ước: thân bài thật ngắn hơn trần 8.000 ký tự
khá nhiều. **Cái giá dung lượng thấp hơn ước tính một nửa** — thêm một lý do để tiếp tục.

⚠️ 4,3MB JSONL là con số **loại trừ** phương án đông lạnh cả vector đoạn vào fixture RS
(`chat_embeddings.jsonl` hiện chỉ 1,4MB). Nó dẫn thẳng tới quyết định 0.4 bên dưới.

---

## 4.2 — RS harness trên pipeline THẬT (98 kịch bản)

Số ở mục 0.3 là **mô phỏng**; đây là số đo qua đúng `_rank` của production với thứ hạng đoạn
đông lạnh (`chat_chunk_ranks.jsonl`). So sánh đúng là cùng 98 câu, `--without-chunks` vs
mặc định:

| | không có tầng đoạn | có tầng đoạn |
|---|---|---|
| **recall@5** (đại lượng nhạy) | 0,832 | **0,900** |
| recall@60 | 0,975 | 0,968 |
| `detail_discovery` r@5 | 0,67 | **1,00** |
| `security` r@5 | 0,88 | 0,94 |
| `open_model` r@5 | 0,78 | 0,89 |

### 🐞 Một lỗi THẬT mà chỉ RS harness bắt được

Lượt đo mô phỏng ở 0.3 **không thấy** lỗi này vì script tự áp cổng "câu rỗng từ khoá" ở
ngoài `_rank`. Khi tầng đoạn chạy qua đúng `_rank` production, `rank-generic`
("Có gì mới không?") tụt **recall@60 1,00 → 0,00**: tin *CISA urges immediate action* rơi
xuống **hạng 109/179**, tức là văng khỏi cả index.

Nguyên nhân: `_rank` tắt tầng vector khi câu hỏi rỗng từ khoá, nhưng bản đầu **quên tắt tầng
đoạn**. Đoạn là văn bản thô nên nhiễu còn mạnh hơn bản phân tích cô đọng — nó đè thẳng tầng
độ quan trọng. Sửa: `chunk_ranks = None` cùng chỗ với `query_vector = None`.

> Bài học lặp lại: **đo một bản sao của pipeline là đo một pipeline không tồn tại.** Cùng loại
> lỗi mà design D4 loại phương án A vì nó.

### Trả giá — 4 câu tụt, ghi rõ

| câu | đại lượng | trước → sau | đọc thế nào |
|---|---|---|---|
| `glo-iot-security` | r@5 | 1,00 → 0,50 | `must_have` chính vẫn hạng 1; tin **thứ hai** rơi 3 → 6 |
| `rank-device-trap` | r@5 | 1,00 → 0,50 | như trên, 4 → 18 |
| `cmp-pq-partial` | r@5 | 1,00 → 0,50 | như trên, 2 → 7 |
| `rank-eol-khai-tu` | **r@60** | 0,50 → **0,00** | ⚠️ nặng nhất — mất chỗ trong **index**, không chỉ trong top-5 |

Ba ca đầu là **đổi thứ tự trong cùng một vùng liên quan**: chỗ nhường lại cho tin cùng chủ đề
khớp sâu hơn ở thân bài, không phải tin đúng bị đẩy ra ngoài.

`rank-eol-khai-tu` là mất mát thật: "công nghệ nào sắp bị *khai tử*" vốn đã là ca đỏ có chủ
đích (embedding không nối thành ngữ đó với *end of support*), và tầng đoạn thêm nhiễu vào
đúng câu mà cả hai tín hiệu cũ đều mù. Giữ nguyên vai trò **mốc đo cho rerank cross-encoder**.

## 5.1 — Vận hành

| | |
|---|---|
| đoạn thật trong DB | **535** / 179 bài (2 lần chạy backfill liên tiếp: lần hai đổi 0 hàng ⇒ idempotent) |
| bảng `document_chunks` | **5,4MB** kể cả HNSW + cột `content` |
| thời gian backfill toàn corpus | **1 phút 55** (535 lượt embed) |
| **độ trễ thêm vào mỗi câu hỏi** | **13ms** trung vị (8,8–16,8ms), kết nối ấm |
| số tin có thứ hạng đoạn / câu | 122–133 (từ `LIMIT 300` đoạn) — rộng hơn `chat_index_top_k`=60 |

Ngưỡng của task 5.1 là 0,5s ⇒ **đạt với biên 38 lần**, không cần mở lại thiết kế `limit`.
Truy vấn đi qua index HNSW, không kéo vector về Python — khác tầng vector mức insight (vốn
kéo ~550KB/câu để giữ `_rank` thuần).

---

## ⚠️ Giới hạn ĐO ĐƯỢC: xếp hạng đúng **chưa đủ để trả lời đúng**

Phát hiện lúc chạy `chat_answer_harness --live` (task 4.3), và nó không hiện ra ở bất kỳ số
đo xếp hạng nào ở trên.

`det-squashfs`: tầng đoạn kéo bài đúng từ hạng 7 lên **hạng 4** — recall@5 tính là THẮNG. Nhưng
câu trả lời thật là **"Không tìm thấy thông tin này trong hệ thống."** Lý do: `CHAT_DEEP_SLOTS`
= 3, nên bài hạng 4 chỉ vào prompt dưới dạng **dòng index nén ~115 token của phần phân tích** —
mà phần phân tích chính là chỗ **không** có chữ `SquashFS`. Model nhìn thấy tiêu đề bài đúng
và vẫn không trả lời được, hoàn toàn hợp lý.

Nói cách khác: **tầng đoạn chữa được TRUY HỒI, còn bằng chứng thì vẫn chỉ đi vào prompt qua ô
sâu (top-3)**. Đây đúng là ranh giới mà `design.md` và spec cố ý dựng ("nội dung phục vụ câu
trả lời vẫn đến từ ô sâu"), nên đây **không phải bug** — nhưng nó giới hạn phần thắng thực tế:

- 13/15 kịch bản `detail_discovery` xếp hạng **≤ 3** ⇒ vào ô sâu ⇒ trả lời được;
- 2/15 (`det-squashfs`, `det-spdx-cyclonedx`) xếp **hạng 4** ⇒ vẫn bị từ chối.

### ✅ ĐÃ ĐÓNG (vòng 2, cùng ngày) — phương án 3

Ba hướng từng cân nhắc: (1) rót đoạn vào khối đã đánh số — **loại**, spec viết "nội dung … SHALL
tiếp tục đến từ cơ chế ô sâu"; (2) nâng `CHAT_DEEP_SLOTS` 3 → 5 — **loại**, thô và bắt **mọi** câu
trả giá độ trễ/token; (3) **đã chọn** — dành một suất ô sâu cho tin có **đoạn khớp nhất toàn
corpus** (`_best_chunk_match`, chỉ nhận hạng đoạn = 1, hoà thì bỏ qua).

Phương án 3 **không** phá ranh giới spec: nội dung vẫn đi qua ô sâu, chỉ đổi *tin nào* được rót.
Và nó không phải heuristic đoán ý định câu hỏi — "đoạn khớp nhất toàn corpus nằm ở bài này" là một
**sự kiện đo được**, không phải phán đoán.

| | trước | sau |
|---|---|---|
| `detail_discovery` AnsRel | 0,73 | **0,93** |
| trả lời được | 12/15 | **15/15** |
| `det-squashfs`, `det-spdx-cyclonedx` | 0,00 | **1,00** |
| `det-arnnotequals` Faithfulness | 0,25 | **1,00** |
| TỔNG AnsRel | 0,92 | **0,95** |

`det-arnnotequals` cho thấy cái gọi là "nhiễu judge" ở lần đo trước **có nguyên nhân thật**: khi
bài vào ô sâu kèm thân bài, câu trả lời có căn cứ và Faith lên thẳng 1,00.

⚠️ **Một nhãn sai đã sửa trước khi chốt.** `det-gpai-annex` hỏi *"nghĩa vụ nhà cung cấp GPAI nằm ở
Annex mấy?"* — **tiền đề sai**: bài ghi nghĩa vụ GPAI ở *Chapter V*, còn Annex I/III là hai đường
phân loại rủi ro cao. Model từ chối **và nêu đúng Chapter V**, tức là trả lời đúng; nhãn mới là cái
sai. Đổi câu hỏi sang *"Hệ thống AI rủi ro cao được liệt kê ở phụ lục nào?"* (0,00 → 1,00). Đây là
tiền lệ **"sửa nhãn, đừng sửa ngưỡng"** của ca blockchain — **khác** `rank-eol-khai-tu`, ở đó sửa
câu hỏi là xoá phép đo.

## Các lỗ hổng khác đã vá cùng ngày

| | vấn đề | cách vá |
|---|---|---|
| #2 | truy vấn đoạn nối tiếp sau embed | gộp `(embed → chunk)` thành một nhánh `asyncio.gather` song song với `list_for_chat`, để phần chờ Postgres che luôn 13ms HNSW |
| #3 | `chat_chunk_ranks.jsonl` mốc im lặng | dòng **meta dấu vân tay** (số đoạn + hằng số chunk + model embedding); `load_chunk_ranks` **NỔ** khi lệch — đã kiểm bằng cách giả lập đổi hằng số |
| #4 | `regenerate_insights` không embed lại | embed lại sau khi ghi đè `signal`/`summary_short`/`topics`; embed lỗi thì **giữ vector cũ**, không set NULL. Lỗi **có sẵn** từ `chat-hybrid-retrieval` |
| #7 | bảng đoạn rỗng → tụt 2 tín hiệu im lặng | `_chunk_ranks` log WARNING kèm lệnh backfill |
| — | nhánh `_chunk_ranks` ném lỗi chưa có test (DoD 3.3) | 2 test mới: exception → `{}`, và `chat_embedding_enabled=false` → không chạm DB |

**#6 `rank-eol-khai-tu` KHÔNG sửa được** và tôi không giả vờ đã sửa: recall@60 vẫn 0,00. Khoảng
cách "khai tử" ↔ *end of support* là ngữ nghĩa thành ngữ, cả ba tín hiệu đều mù; chữa bằng cách sửa
câu hỏi cho gần chữ trong tin là xoá phép đo. Giữ nguyên làm mốc cho rerank cross-encoder.

## 4.3 — Chất lượng câu trả lời (`--live`, 98 kịch bản)

| | kết quả | ngưỡng |
|---|---|---|
| **Faithfulness** | **0,99** | ≥ 0,95 ✅ |
| **Citation Precision** | **1,00** | = 1,00 ✅ |
| Answer Relevance | 0,92 | baseline 0,93 ± 0,05 ✅ |
| từ chối đúng | 5/5 | |
| lệch mode | 0/98 | |

**VERDICT: PASS.** Baseline đã chốt lại kèm lý do trong `chat_answer_harness.BASELINE_META`.

### ⚠️ Hai lần "bộ đo nói dối" phải sửa trước khi tin vào số

Cả hai đều là lỗi **phép đo**, không phải code sản phẩm — và cả hai đều im lặng.

**(a) Harness đo một pipeline khác production.** `_FixtureSession` chỉ phục vụ
`select(Insight)`, nên truy vấn đoạn ném lỗi → `_chunk_ranks` nuốt lỗi → rơi về hai tín hiệu.
Đúng thiết kế suy giảm êm, nhưng nghĩa là lượt `--live` đầu tiên chấm một pipeline **không có
tầng đoạn** mà không báo gì; chỉ phát hiện được vì log đầy dòng *"Truy hồi mức đoạn lỗi"*.
Sửa: tiêm thứ hạng đoạn đông lạnh vào `_make_service`.

**(b) Fixture thiếu thân bài cho câu toàn cục.** `_wanted_anchor_ids` chỉ lấy content cho
`anchor_insight_id`, trong khi từ `chat-context-depth` thì ô sâu rót `normalized_content` cho
tin xếp hạng cao của **bất kỳ** câu toàn cục nào. Hệ quả: ba kịch bản `detail_discovery` xếp
**hạng 1** — tức đã nằm trong ô sâu — vẫn bị chấm "từ chối", chỉ vì fixture không có gì để rót.

Sau khi bổ sung thân bài cho 9 bài còn thiếu:

| | trước | sau |
|---|---|---|
| `detail_discovery` AnsRel | 0,57 | **0,73** |
| trả lời được | 10/15 | **12/15** |
| `det-rabbitmq-c2`, `det-hmac-agent` | 0,00 | **1,00** |
| `det-chunking-strategy` | 0,50 | 1,00 |

Ba ca còn từ chối đúng là ba ca nằm **ngoài `CHAT_DEEP_SLOTS`=3** (`det-squashfs` hạng 4,
`det-spdx-cyclonedx` hạng 5) hoặc không rút được câu trả lời từ ô sâu (`det-gpai-annex`) —
khớp chính xác với giới hạn mô tả ở mục trên.

> Bài học chung của cả (a) và (b): **suy giảm êm khiến bộ đo hỏng một cách im lặng.** Đường
> fallback được thiết kế để production không bao giờ gãy, và nó phục vụ harness y hệt — nên
> harness phải được tiêm dữ liệu thật, không được để nó tự rơi vào nhánh dự phòng.

`det-arnnotequals` Faith 0,75 → 0,25 là **nhiễu judge**, không phải bịa: câu trả lời bám sát bài
(nêu đúng `signin:PrincipalArn` ở giai đoạn tiền xác thực vs `aws:PrincipalArn` hậu xác thực),
judge chê cách diễn đạt "chặn" vs "loại trừ" và một verdict của nó bị cụt giữa chừng.

---

## Công cụ trong `eval/`

| file | vai trò |
|---|---|
| `mine_detail_terms.py` | đào định danh chỉ có trong thân bài (task 0.1) |
| `detail_scenarios.jsonl` | 15 kịch bản đã gán nhãn tay — **đã land** vào `chat_scenarios.jsonl` |
| `measure_detail_rank.py` + `detail_rank_result.json` | số đo cổng chặn (task 0.2) |
| `simulate_chunk_signal.py` + `simulate_chunk_result.json` | bằng chứng triển vọng (task 0.3) |

⚠️ `chunk_embeddings.jsonl` (4,3MB vector đoạn) **cố ý không commit**: nó là bộ nhớ đệm một lần
của lượt mô phỏng 0.3, và quyết định D4 đã loại hẳn phương án đông lạnh vector đoạn vào fixture.
Chạy lại `simulate_chunk_signal.py` sẽ sinh lại nó (~40s, vài xu). Thứ được commit là bảng
**thứ hạng** đông lạnh — `backend/tests/eval/chat_chunk_ranks.jsonl`, 0,6MB.
