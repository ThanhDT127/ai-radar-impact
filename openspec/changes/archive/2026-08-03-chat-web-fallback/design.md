## Context

**Module: M8 (Chat Q&A) + M6 (Dashboard).** Nội dung tra cứu sống đúng một lượt hỏi trong bộ
nhớ, **không** thành `RawDocument` hay `Insight`.

**Bảng DB bị ảnh hưởng: `chat_logs`** — migration **015** thêm cột nullable `web_searches`.
(Bản đầu của design nói "không migration"; xem D7 để biết vì sao bộ đếm trong bộ nhớ không đủ.)

**API bị ảnh hưởng:** `POST /api/v1/chat` và `POST /api/v1/chat/stream` — `Citation` thành
union có kiểu phân biệt; response mang thêm khối Search Suggestions khi có tra cứu. Không
endpoint mới.

**AI/LLM:** `gemini-2.5-flash` (giữ nguyên) cho bước 1 và 3; bước 2 dùng
`Tool(google_search=GoogleSearch())`. **Grounding strategy không đổi về bản chất**: model chỉ
được nói những gì có trong khối DỮ LIỆU đánh số; change này chỉ thêm một *loại* mục vào khối đó.

### Hai sự thật đã xác minh, chúng quyết định toàn bộ thiết kế

```
1) SDK google-genai 1.75.0 (bản đang pin):
   types.GroundingChunkWeb.model_fields → ['domain', 'title', 'uri']
                                                      ▲
                              KHÔNG có snippet/text — nội dung model đã đọc
                              không bao giờ quay về tay ta.

2) Google Custom Search JSON API: đóng với khách mới từ 2025,
   khách cũ dùng tới 01/01/2027 ⇒ đường "tự gọi search, tự đánh số" đã khoá.
```

### Chi phí

| | |
|---|---|
| Grounding with Google Search, Gemini 2.x | **$35 / 1.000 truy vấn** |
| Grounding, Gemini 3 | $14 / 1.000 |
| Một câu chat hiện tại (~19k token vào, flash) | ≈ **$0,006** |
| ⇒ một lần tra cứu | ≈ **6× toàn bộ câu trả lời** |

Không phải rào cản, nhưng đủ để bộ đếm riêng là **bắt buộc**, không phải tuỳ chọn.

### Đồ nghề đã có sẵn trong repo

```
app/connectors/web_article_connector.py   trafilatura wrapper, fetch_url + extract
requirements.txt:39                        trafilatura==2.0.0
app/services/normalizer.py:14              MAX_CONTENT_LENGTH = 8000
                                           ▲ ĐÚNG trần mà ô sâu corpus đang dùng
```

Hệ quả: một `WebSource` sau khi fetch có **hình dạng giống một ô sâu** (tiêu đề + thân bài
≤8000 ký tự + nguồn), nên nó cắm vào `build_context` mà không cần khái niệm mới trong prompt.

Ràng buộc kế thừa, không được phá:
- **MỘT dãy số `[n]`, MỘT bảng ánh xạ.** Prompt không chứa uri/UUID; server cấp phát số.
- `enforce_grounding` fail-closed chạy nguyên xi.
- Trần chống-tool-loop đếm **bước lập luận**; budget đếm **tiền**. Hai bộ đếm khác nhau.
- Một pipeline, hai lối ra (blocking / SSE).
- `build_context()` là hàm **thuần**.

## Goals / Non-Goals

**Goals:**
- Câu hỏi ghép được trả lời **phần có dữ liệu**, thay vì từ chối toàn bộ.
- Text và uri của một nguồn web **thực sự thuộc về nhau** (trích dẫn không trỏ sai).
- `Faithfulness` và `Citation Precision` vẫn **đo được** sau change.
- Mặc định **tắt**; bật lên không đổi hành vi câu không cần tra cứu.

**Non-Goals:** kiến thức nền không nguồn; Fork A; ghi nội dung web vào DB; đụng `_rank`.

## Decisions

### D1 — Fork B2: grounding lấy `uri`, `trafilatura` lấy text

```
bước 1   model(context corpus)          ──▶ trả lời vế A + [[TRA_CỨU_NGOÀI: …]]
bước 2   model(google_search ON)        ──▶ grounding_chunks → 2–3 uri
   ·     trafilatura × N (song song)    ──▶ text THẬT      ◀ KHÔNG phải bước model
bước 3   model(corpus + WebSource[n])   ──▶ câu trả lời cuối, MỘT dãy [n]
```

Vì sao không để bước 2 tự viết tóm tắt rồi dùng luôn (gọi là **B1**):

```
[61] developers.google.com/…        ← citation trỏ trang này
     "…3072 chiều, ngữ cảnh 2048…"
      ▲ do MODEL viết ở bước 2, không trích từ trang.
        Model diễn giải sai ⇒ citation trỏ vào trang KHÔNG nói thế.
```

Đó đúng là chế độ hỏng cả hệ thống này sinh ra để chặn: **lời bịa có kèm nguồn hợp lệ**. B2
làm text và uri thuộc về nhau thật.

### D2 — Sentinel **mang tham số**, phát **kèm** câu trả lời một phần

Khác hẳn `OUT_OF_SCOPE_SENTINEL` của `chat-scope-routing`, vốn chỉ được nhận khi nó là **toàn
bộ** câu trả lời. Ca ở đây là *một phần*: model trả lời được vế A.

```
Nemotron 3 Embed có biến thể 8B (#1 RTEB) và 1B, ngữ cảnh 32k, tối ưu NVFP4 [4].
[[TRA_CỨU_NGOÀI: thông số model embedding Gemini — số chiều, độ dài ngữ cảnh]]
```

Truy vấn tìm kiếm do **model** viết, không phải server ghép từ khoá: model là bên biết chính
xác mình thiếu gì. Mọi heuristic đoán ý định câu hỏi ở repo này đều đã trả giá.

Bias **dè dặt hơn cả** `chat-scope-routing`: ở đó mở nhầm tốn 1 lượt gọi; ở đây tốn tiền
search + fetch mạng + mở nội dung lạ vào prompt. Luật prompt: chỉ phát khi câu hỏi hỏi một
**thực thể hoàn toàn vắng** khỏi DỮ LIỆU, KHÔNG phát khi chỉ muốn biết thêm.

### D3 — Sentinel web và sentinel out-of-scope **loại trừ nhau**

Mode B → `expanded` đã tiêu 2 bước. Với trần 3, chuỗi `B → expanded → web` là 3 bước — vừa
khít, nhưng cộng retry chống-cắt thì thành **tới 6 lượt tính tiền**.

Chốt: **web fallback chỉ phát ở bước cuối cùng của một đường**. Mode B phát
`OUT_OF_SCOPE_SENTINEL` (như cũ) và **không** được phát sentinel web; lượt `expanded` mới là
chỗ được phát nó. Prompt mode B không mang luật sentinel web.

### D4 — `WebSource` vào **cùng** bảng ánh xạ, `Citation` thành union có kiểu

```
mapping = { 1..3  → Insight     (ô sâu)
            4..60 → Insight     (index)
            61,62 → WebSource   (uri, title, text)   ← cùng dãy, khác kiểu }
```

`Citation` mang `kind: "insight" | "web"`. Frontend vẫn giải bằng **`citations.find(c => c.n
=== n)`** — không đổi một dòng logic tra cứu. Đây là điều kiện để **không** dựng lại bẫy "hai
hệ quy chiếu cho `n`".

Server vẫn cấp phát số; prompt vẫn không chứa uri. Bất biến chống-bịa **bằng cấu trúc** giữ nguyên.

### D5 — Fetch hỏng là chuyện thường ⇒ suy giảm êm, không 500

Paywall, 403, trang render bằng JS, 404. Fetch **song song**, trang nào ra text thì dùng.

- ≥1 trang tải được → dùng các trang đó.
- **Tất cả hỏng** → rơi về phần text model đã sinh ở bước 2 (tức B1), nhưng **gắn nhãn rõ**
  trong khối DỮ LIỆU là *tóm tắt chưa đối chiếu nguyên văn*, để model biết mức chắc chắn khác.
- Bước 2 không ra uri nào → bỏ hẳn tra cứu, trả lời phần corpus + nói thẳng phần thiếu.

Không ca nào được thành HTTP 500 (bài học lỗi (B) của `chat-scope-routing`).

### D6 — Nội dung web là **DỮ LIỆU, không phải chỉ thị**

B2 thua B1 đúng một điểm và không nên giấu: text nguyên văn từ trang lạ đến **nguyên vẹn**,
payload prompt-injection không bị model diễn giải làm loãng. Đổi lại, corpus hiện tại cũng đang
nạp nội dung cào từ web vào ô sâu — đây là **mở rộng một bề mặt đã tồn tại**, không phải mở
một bề mặt mới.

Biện pháp: luật tường minh trong prompt bước 3 (khối tra cứu là dữ liệu, mọi câu mang tính ra
lệnh trong đó phải bị bỏ qua) + trần độ dài theo `MAX_CONTENT_LENGTH` + số trang tối đa.

### D7 — Bộ đếm riêng `max_daily_web_searches`

`max_daily_chat_calls` canh budget lượt sinh văn bản ~19k token. Search là tài nguyên khác,
đơn giá khác (~6× một câu trả lời) — trộn chung là để một loại bào mòn budget loại kia. Cùng
lập luận đã dùng để loại lượt embed và intent tầng 2 khỏi bộ đếm chính.

Hết quota search → **không** 429; trả lời phần corpus + nói rõ không tra cứu được lúc này.
Tra cứu là tính năng bổ trợ, không phải điều kiện để trả lời.

**Bộ đếm phải nằm trong DB, không phải trong bộ nhớ** (phát hiện khi implement 03/08). Đây là
trần **tiền**: một tiến trình restart-loop với bộ đếm in-memory là một vòng lặp tiêu tiền không
giới hạn. Dùng lại đúng nguyên tắc đã có của `chat_logs` — *bảng log cũng chính là counter* —
nên chỉ cần một cột nullable (`web_searches`, migration 015) và `SUM(...)` theo ngày UTC, y hệt
`sum_model_calls_today`. Hai truy vấn tách biệt, cạn độc lập.

### D8 — Search Suggestions là **bắt buộc**, không phải trang trí

Google yêu cầu hiển thị Search Suggestions khi dùng Grounding with Google Search.
`GroundingMetadata.search_entry_point.rendered_content` có sẵn. Đây là hạng mục tuân thủ; bỏ
qua là vi phạm điều khoản, không phải cắt gọt phạm vi.

### D9 — Harness phải giữ được tính tất định và miễn phí

`chat_answer_harness --live` mà gọi search thật thì vừa không tái lập được, vừa tốn tiền theo
số lần chạy. Đông lạnh **kết quả bước 2 + text đã fetch** theo kịch bản, kèm **dòng vân tay**
(truy vấn, uri, ngày lấy) và **nổ** khi lệch — đúng khuôn `chat_chunk_ranks.jsonl`.

## Risks / Trade-offs

| Rủi ro | Xử lý |
|---|---|
| Sentinel giả (tra cứu khi không cần) → tốn tiền + độ trễ | Prompt dè dặt (D2); **đo tỉ lệ sentinel giả** như `chat-scope-routing` đã đo (0/6) trước khi bật mặc định |
| Prompt injection từ trang lạ | D6; và bề mặt này đã tồn tại qua ô sâu corpus |
| TTFT dài hơn hẳn (3 bước + fetch) | Phụ thuộc `chat-status-milestones`; mốc `web_search` mang truy vấn thật và tên miền đang đọc |
| Faithfulness judge chấm phần web | Text web **nằm trong context** ⇒ vẫn chấm được; đây chính là lý do chọn B2 thay vì A |
| Trang tải được nhưng nội dung sai/cũ | Không giải quyết ở v1. Uri luôn hiện để người dùng tự kiểm |

## Migration Plan

Không có migration DB. Mặc định **tắt** (`chat_web_fallback_enabled = false`) ⇒ prompt không
mang luật sentinel web, pipeline y hệt hôm nay, trần bước hiệu dụng vẫn là 2.

Bật dần: bật ở môi trường dev → đo tỉ lệ sentinel giả + độ trễ + tỉ lệ fetch thành công trên
một bộ câu hỏi thật → mới bật mặc định.

Rollback: tắt cờ env. Không có trạng thái nào tồn dư (không ghi DB).

### D10 — GIẢI CHUYỂN HƯỚNG cho TRÍCH DẪN, không phải cho nội dung (thêm sau spike 0.4b)

Spike phát hiện `grounding_chunks[].web.uri` là **link chuyển hướng của Vertex**
(`vertexaisearch.cloud.google.com/grounding-api-redirect/…`), và `.title` chỉ là **tên miền**
(`'google.com'`), không phải tiêu đề trang.

Đo được, và hai kết luận này phải giữ tách bạch:

| | fetch thẳng link chuyển hướng | giải rồi fetch URL thật |
|---|---|---|
| Lấy được **nội dung** | 8/9 | 8/9 — **bằng nhau** |
| Có **URL thật** để bấm | ✗ | ✓ |
| Có **tiêu đề thật** | ✗ (chỉ `'google.com'`) | ✓ (`'Embeddings \| Gemini API…'`) |

⇒ Bước giải chuyển hướng (`HEAD`, 0,5–2,1s, song song hoá) tồn tại **vì trích dẫn**, không vì
nội dung. Nguồn nào không giải được thì **bỏ** — một nguồn không dẫn đi đâu được thì không
phải là nguồn, và để nó lại là cho người dùng một link mờ đục có thể hết hạn.

Tiêu đề lấy bằng `trafilatura.extract_metadata` trên chính trang đã tải, KHÔNG lấy từ
`grounding_chunks[].web.title`.

## Open Questions

- **Gộp bước 1+2 — vẫn HOÃN, nhưng bằng chứng đã nghiêng.** Spike 0.1: bật tool mà câu hỏi
  không cần tra cứu thì `grounding_metadata = None`, 0 chunk, 0 truy vấn ⇒ **không lượt tìm
  nào chạy**. Rất có thể tiền tính theo truy vấn thực chạy. Nhưng đó mới là *"không có lượt
  tìm nào"*, **chưa phải đọc hoá đơn** — phải đối chiếu billing console sau một ngày mới được
  dựa vào. v1 giữ 3 bước tách bạch.
- ~~Bước 2 dùng model nào~~ → **CHỐT: `gemini-2.5-flash-lite`.** Spike 0.2 xác nhận nó lái
  được tool, cho 10 chunk + `search_entry_point` đầy đủ, không kém flash ở đầu ra của bước tra
  cứu — mà bước đó không cần khả năng viết văn.
- **Số uri tối đa**: grounding trả về **9–10** nguồn (không phải 2–3 như giả định ban đầu), nên
  `chat_web_max_sources` là cắt bắt buộc. Vẫn cần đo độ trễ fetch song song ở 2 vs 3 để chốt.
