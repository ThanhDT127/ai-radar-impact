# Design: chatbot-qa

## Đã đổi so với bản 15/07 (respec 22/07/2026)

| Bản 15/07 giả định | Thực tế đo được | Quyết định mới |
|---|---|---|
| Bot transport Telegram có sẵn | Gỡ sạch 21/07 — 0 dòng `telegram` trong `backend/app` | Bỏ `chat-telegram-surface`, bỏ D7 (`chat_sessions`) |
| Người nhận định danh `chat_id` | `subscribers.email` (migration 010) | History stateless hoàn toàn, không có bảng session |
| Chưa có Vertex key → không test E2E | Vertex chạy thật; 179 insight sinh 21/07 | Bỏ hết dấu **[cần key]** |
| `response_schema` chống bịa citation | Bật schema cho output dài → runaway → 16/16 doc lỗi (đo 20/07) | D4 đổi hẳn cơ chế: server giữ citation |
| Function-calling 2-4 lượt, $0.015–0.025 | Cả corpus 179 tin = 19.3k token = $0.007, 1 lượt | D3 đổi sang index-in-context |
| Mode B đọc full text, cap 30.000 ký tự | `normalizer.MAX_CONTENT_LENGTH = 8000` cắt ngay từ ingest; max thật = 8000 | D2 bỏ cap, viết lại lý do tồn tại |
| Cột `raw_documents.content` | Cột thật là `normalized_content` | Sửa tên khắp spec/tasks |
| "Thêm method `chat()`" là đủ | `GeminiClient` sync toàn bộ (`time.sleep`) | D6 thêm `asyncio.to_thread` + singleton |

## Context

**Số đo trên DB ngày 22/07/2026** (179 insight `published` + `is_primary`):

```
cửa sổ thời gian          độ dài trường (ký tự, trung bình)      recommendations[role].urgency
  7 ngày ····· 107          title ············  60                 phủ 179/179 (100%)
 30 ngày ····· 159          signal ···········  144                496 entry: 86 high / 313 med / 97 low
 90 ngày ····· 175          so_what ··········  133
 toàn bộ ····· 179          summary_medium ···  508              normalized_content
 không ngày ··   0          roles/insight ····    3                p50 4177 · p90 8000 · max 8000
                            topics/insight ···    3                rỗng 0/179 · >6000 ký tự: 66/179
```

Hiện trạng code liên quan:

- `GeminiClient` (`app/ai/gemini_client.py`) **sync toàn bộ** — `generate_content` blocking +
  `time.sleep()` trong vòng retry. Vô hại trong script/scheduler, chí mạng trên request path.
- Quota guard W1 đếm **tài liệu** (`RawDocumentRepository.count_analyzed_today()` theo `analyzed_at`),
  không đếm lượt gọi model. Comment `analyzer.py:24` ghi rõ chủ ý bỏ counter RAM để quota sống sót
  qua restart.
- `InsightRepository.list_paginated` có filter `roles`, `urgency`, `momentum`, `vietnam_relevance`,
  `intelligence_tier`, `search` (ILIKE) — **thiếu** `topics` và cửa sổ thời gian.
- `delivery_engine.score_for_role()` đã hiện thực hoá đúng luật xếp hạng cần cho chat, đọc JSONB
  bằng Python trên một cửa sổ đã load sẵn.
- `normalizer.MAX_CONTENT_LENGTH = 8000` — trần cứng nội dung, áp ngay lúc ingest.
- `RawDocumentRepository.tombstone_older_than()` set `normalized_content = None` sau
  `retention_months` (6) nhưng **giữ insight**.
- Frontend: 3 route (`/`, `/insights/:id`, `/subscribers`), `Layout.tsx` bọc tất cả; `InsightDetail`
  đã có split-view 50/50 hiện sẵn bản gốc.

**Module ảnh hưởng:** M8 Chatbot/Search (chính), M5 Insight Repository (đọc), M10 Governance (quota,
log). **Không liên quan** M7 Delivery (quyết định 22/07: email và chat không nối vào nhau) và n8n.

## Goals / Non-Goals

**Goals:**
- Một chat service 2 chế độ trên 1 endpoint, grounded, citation không thể bịa.
- Chat không làm analysis pipeline chết đói quota, và không chặn event loop của API.
- Ship theo pha: mode B trước (1 lần gọi, khó sai), mode A sau (cũng 1 lần gọi, chỉ khác cách dựng context).

**Non-Goals:**
- Function-calling / tool loop; vector search; trang `/chat` riêng; conversation store; streaming;
  đổi provider hoặc nâng pin SDK; cầu nối email→chat; auth mới.

## Decisions

### D1. Một endpoint `POST /api/v1/chat`, `insight_id` optional

Giữ nguyên quyết định cũ. Mode B là trường hợp con của mode A về pipeline trả lời (chỉ khác cách dựng
context) → chung endpoint, chung prompt scaffolding, chung quota check; UI chỉ đổi 1 param khi gắn/bỏ
context chip.

**Request:** `{ question: str, history: [{role, content}] (cap 10), insight_id?: UUID }`
**Response:** `{ answer: str, citations: [{insight_id, title, source_url}], mode: "insight"|"global" }`

### D2. Mode B: nhét cả bài gốc, không cap — và lý do tồn tại đã viết lại

Context = `title`, `signal`, `so_what`, `why_it_matters`, `recommendations`, `risks`,
`summary_medium` + **toàn bộ** `raw_documents.normalized_content`. Không cần cap: trần 8000 ký tự đã
áp từ ingest, đo thật max = 8000 (≈2.7k token). Tổng ~3.1k token ≈ **$0.002/câu**.

**Lý do tồn tại của mode B — bản trung thực.** Bản 15/07 biện minh bằng "trả lời được chi tiết mà
analysis đã cắt ở 6000 ký tự". Đo thật thì phần "bị giấu" tối đa **2000 ký tự** và chỉ tồn tại ở
**66/179 doc (37%)**; hơn nữa `InsightDetail` đã hiện sẵn bản gốc ở split-view. Giá trị thật của mode
B là **hỏi một câu thay vì đọc 4000 chữ**, và hỏi được câu mà card không trả lời sẵn ("chỗ này áp
dụng cho stack của mình thế nào?"). Đừng bán nó như tính năng mở khoá nội dung ẩn — sẽ vỡ ngay câu
hỏi đầu tiên lúc demo.

*Alternative bị loại:* chỉ dùng insight fields — rẻ hơn $0.0005 nhưng bot không nói được gì ngoài
cái card đã hiển thị.

**Cạm bẫy đã biết:** `tombstone_older_than` xoá `normalized_content` sau 6 tháng nhưng giữ insight.
Hiện 0/179 rỗng, nhưng từ khoảng tháng 11/2026 sẽ xuất hiện. Mode B gặp content rỗng SHALL chạy bằng
insight fields và nói rõ "bài gốc đã hết hạn lưu trữ" — không im lặng trả lời như thể vẫn có bài.

### D3. Mode A: server-driven retrieval — lọc, xếp hạng, index nén, 1 lần gọi

```
câu hỏi
   │
   ├─▶ server lọc: status=published AND is_primary AND published_at >= now - CHAT_WINDOW_DAYS
   │
   ├─▶ server xếp hạng bằng score_for_role() (dùng lại delivery_engine, không viết lại)
   │
   ├─▶ dựng index nén, đánh số [1..N]:
   │     [n] | title | signal | roles | topics | ngày        ≈ 295 ký tự ≈ 108 token/dòng
   │     KHÔNG có UUID trong prompt — server giữ bảng n → insight_id (xem D4)
   │
   └─▶ 1 lần gọi Gemini: system prompt + index + history + câu hỏi → text thuần có [n]
```

**Vì sao không function-calling.** Đo trên corpus thật:

| Cửa sổ | Insight | Token index | Chi phí/câu (in+out) | Lượt gọi |
|---|---:|---:|---:|---:|
| 7 ngày | 107 | 11.6k | $0.005 | 1 |
| 30 ngày | 159 | 17.2k | $0.006 | 1 |
| toàn bộ | 179 | 19.3k | **$0.007** | **1** |
| _(D3 cũ: function-calling)_ | — | — | _$0.015–0.025_ | _2–4_ |

**Đo thật 22/07/2026 (n=3, corpus 179 tin) — ước tính input chuẩn, chi phí thì KHÔNG:**

| Câu hỏi | input | output | thinking | thời gian | chi phí |
|---|---:|---:|---:|---:|---:|
| "tin bảo mật tuần này" | 19.126 | 223 | **3.791** | 22,6s | $0,0157 |
| "cổ phiếu Vinamilk" (ngoài corpus) | 19.125 | 10 | 121 | 5,0s | $0,0061 |
| "lỗ hổng cần vá gấp" | 19.123 | 239 | 1.751 | 12,5s | $0,0107 |

Input 19,1k — lệch **1%** so với ước tính 19,3k, nên phần tính toán index của D3 đứng vững. Nhưng
**thinking tokens của Gemini 2.5 bị tính tiền như output** ($2,50/1M) và bản design không hề tính tới:
chi phí thật **$0,006–0,016/câu** (tb ~$0,011) thay vì $0,007, độ trễ **5–22,6s** thay vì 3-6s
(15 câu qua HTTP: trung bình 9,7s). Thinking dao động 121 → 3.791 token tuỳ độ khó câu hỏi và là
biến chi phối cả tiền lẫn thời gian.

**Quyết định D3 vẫn đứng**, thậm chí mạnh hơn: function-calling phải trả thinking trên **mỗi** lượt
trong 2-4 lượt, với context lớn dần — tức khoảng $0,03-0,06/câu. Index-in-context vẫn rẻ hơn 3-5 lần.

**Van xả chưa dùng được:** `thinking_budget` cần `google-genai` 1.x; bản pin 0.8.0 chỉ có
`ThinkingConfig(include_thoughts)`, không chỉnh được ngân sách. Nâng SDK là non-goal của change này
(rủi ro cho pipeline analysis vừa đo đạc). Đây là ứng viên số 1 cho change kế tiếp — tắt/giới hạn
thinking sẽ kéo cả chi phí lẫn độ trễ xuống ~1/3.

Rẻ hơn 2-3 lần, nhanh hơn 3-4 lần, và xoá luôn cả một lớp lỗi: model không chọn filter thì không
chọn sai filter. Bản 15/07 loại phương án này với lý do "nhét N insight gần nhất vào context không
trả lời được câu hỏi có điều kiện" — đúng với *N bài gần nhất, full text*, sai với *index nén có
metadata*: điều kiện role/topic/thời gian nằm ngay trong index, model lọc bằng cách đọc.

**Sức chịu khi corpus phình.** Nhịp suy từ `published_at` 3 tuần gần nhất (45/76/24) ≈ **48 tin/tuần**
→ trạng thái ổn định ở `retention_months=6` khoảng **1250 tin** → 135k token → ~$0.042/câu (vẫn dưới
ngưỡng 200k của Flash). Van xả: hạ `CHAT_WINDOW_DAYS` xuống 90 → ~625 tin → 67k token → ~$0.021/câu,
vẫn 1 lượt gọi. Mặc định v1: `chat_window_days = 0` (không giới hạn — cả corpus lọt thoải mái).
Khi nào một cửa sổ 90 ngày cũng không đủ thì mới quay lại function-calling.

**Trần top-K (thêm 22/07/2026 sau khi đo).** Câu trả lời trích tối đa 5 tin, nên gửi cả 179 tin để
chọn ra 5 là lãng phí. Cắt index ở `chat_index_top_k = 60` sau khi xếp hạng:

```
top-179 | 19.126 in | 3.930 think | 23,0s | $0,0160
top-60  |  6.670 in | 2.534 think | 15,0s | $0,0090     −44% chi phí · −35% thời gian
```

Đây là van xả **chính**, tốt hơn `chat_window_days`: cắt theo *thứ hạng* nên chi phí phẳng khi corpus
phình, còn cắt theo *thời gian* thì cửa sổ 90 ngày ở corpus 1250 tin vẫn còn ~625 tin.

**⚠️ Cạm bẫy đã sập một lần — top-K chỉ an toàn khi xếp hạng biết câu hỏi.** Lần đầu bật top-60 với
xếp hạng thuần `score_for_role` (đo độ quan trọng chung, mù với nội dung câu hỏi): recall tin liên
quan rớt còn **42%**, riêng câu "mô hình mã nguồn mở" còn **2/18 tin (11%)** — tin chủ đề ngách
thường urgency thấp nên nằm hết ở đuôi và bị cắt sạch. Nguy hiểm nhất là nó **im lặng**: bộ 15 câu
kiểm thử vẫn "đạt" vì model trả lời trôi chảy từ 2 tin sót lại, không có tín hiệu nào báo 16 tin kia
tồn tại. Sau khi trộn độ liên quan vào khoá xếp hạng (xem D7): **91%**.

Bài học tổng quát: đây đúng kiểu lỗi D3 muốn tránh khi từ chối để model chọn filter — chỉ khác là
**server** mới là bên lọc sai. Cắt bớt ứng viên chỉ hợp lệ khi tiêu chí cắt cùng trục với câu hỏi.

**Tầng fetch chi tiết (tuỳ chọn, do server điều khiển).** Câu hỏi cần chiều sâu ("so sánh 2 tin này")
có thể chạy lượt 2: server nạp `summary_medium`/`normalized_content` của các `[n]` mà lượt 1 đã trích
dẫn rồi gọi lại. Trần cứng **2 lượt gọi/câu hỏi**. v1 chưa bật; giữ chỗ trong `chat_logs.model_calls`.

*Alternatives bị loại:* (a) function-calling — đắt hơn, chậm hơn, thêm bề mặt lỗi ở quy mô này;
(b) pgvector — thêm hạ tầng + backfill embeddings trong khi 179 tin lọt gọn vào một prompt.

### D4. Grounding: server cầm citation, model chỉ đánh dấu

```
Mode B:  đúng 1 candidate (insight đang mở)
         → citation = insight đó, model KHÔNG cần phát ra định danh nào
         → xác suất bịa = 0 theo cấu trúc

Mode A:  server đánh số candidate và giữ bảng  n → insight_id  ở phía mình
         → model trả TEXT THUẦN, trích dẫn bằng [n]
         → service regex [n] → tra bảng → dựng citations đầy đủ (id, title, source_url)
         → [n] ngoài phạm vi → bỏ marker đó, GIỮ câu trả lời
```

Model không bao giờ nhìn thấy UUID, nên không có gì để bịa. Đây là thay thế cho cơ chế cũ
("model trả `citation_ids`, service lọc id lạ") — chống bịa **bằng cấu trúc thay vì hậu kiểm**, và
tiện thể tiết kiệm ~12 token/dòng index.

**Bỏ `response_mime_type=application/json` cho chat.** Bài học đo được 20/07 (`gemini-structured-output`):
bật `response_schema` cho lần gọi có output dài làm model sinh lan man tới chạm `max_output_tokens`
rồi bị cắt giữa chuỗi → 16/16 doc lỗi `Unterminated string`; `max_length` trong schema Vertex **không
thực thi**. Câu trả lời chat chính là dạng output dài không giới hạn — đúng hình dạng đã gây vỡ. Trả
text thuần thì không có JSON để vỡ.

Hệ quả kèm theo:
- `max_output_tokens` cho chat = **4096**. Ban đầu đặt 2048; đo thật 22/07/2026 cho thấy không đủ —
  Gemini 2.5 tính **thinking tokens vào cùng ngân sách output**, và câu hỏi kiểu "liệt kê tin bảo mật
  tuần này" sinh ~1150 token nhìn thấy được, cộng thinking là chạm trần rồi bị cắt giữa từ. Kèm theo:
  `finish_reason == MAX_TOKENS` phải được phát hiện và nói ra cho người dùng, không trả về nửa câu
  như thể đã xong.
- `temperature = 0.2`.
- **Fail-closed đổi định nghĩa**: không còn "không có citation hợp lệ → chặn". Luật mới: câu trả lời
  mang tính khẳng định mà **không có marker `[n]` nào** → thay bằng thông báo không đủ căn cứ. Câu
  trả lời dạng "không tìm thấy trong hệ thống" được đi qua với `citations = []`.

### D5. Quota: bảng `chat_logs` vừa là log vừa là counter

```
chat_logs(id UUID PK, mode VARCHAR(10), model_calls INT, citations_count INT,
          latency_ms INT, created_at TIMESTAMP)

budget dùng trong ngày = SELECT COALESCE(SUM(model_calls),0)
                         FROM chat_logs WHERE created_at >= đầu ngày UTC
```

Bảng log của "task hoàn tất" và counter quota là **cùng một artifact** — không cần bảng thứ hai. Nó
cũng thay chỗ migration `chat_sessions` đã chết, nên vẫn đúng 1 migration.

Ba chi tiết dễ sai, ghi rõ ở đây:
1. **Ghi row trong `finally`**, không phải chỉ khi thành công. Một call trả về rồi vỡ parse **vẫn bị
   tính tiền** — không log là quota rò rỉ. Ngược lại, retry 429 (không có response) không tính.
2. **Chấp nhận overshoot.** Check trước → gọi → log sau, hai request đồng thời có thể cùng lọt. Budget
   mềm nội bộ lố vài lượt là vô hại; thêm reservation/lock là over-engineering.
3. **Đếm theo UTC**, khớp `count_analyzed_today()`. Đừng một cái UTC một cái giờ VN.

**Đơn vị đo lệch nhau — phải ghi comment.** `max_daily_analysis = 500` đếm **tài liệu**, mà 1 tài liệu
= gate call + analyze call = **2 lượt gọi model** → 500 "đơn vị" thực chất ~1000 lượt gọi.
`max_daily_chat_calls` đếm **lượt gọi**. Hai số dưới cùng cái tên "quota guard" nhưng khác đơn vị gấp
đôi. Không sửa cái cũ (code đã được đo đạc), chỉ ghi chú.

**Rủi ro budget-ngày không cứu được: va chạm RPM.** Scheduler chạy 7/13/19h VN; 13h là giữa giờ làm
→ chat và batch analysis bắn Vertex cùng lúc. Analysis có retry backoff nên sống sót nhưng chậm lại.
Chấp nhận ở v1 vì chat chỉ 1-2 lượt gọi/câu.

**Dashboard không có auth** — ai vào được là đốt được budget. Quota là hàng rào duy nhất, nên
`max_daily_chat_calls` mặc định đặt khiêm tốn (**200**) và tăng khi cần.

### D6. `GeminiClient.chat()`: `asyncio.to_thread` + singleton

Chat nằm trên **request path** của FastAPI async. Gọi thẳng `generate_content` blocking sẽ đóng băng
event loop 3-6s mỗi câu hỏi → cả dashboard đứng hình cho mọi người dùng khác.

| Hướng | Được | Mất | Chọn |
|---|---|---|---|
| `asyncio.to_thread` bọc call sync | 0 dòng sửa logic hiện có, độc lập với phiên bản SDK | mỗi câu giữ 1 thread 3-6s | ✅ |
| `client.aio` native | sạch, không thread | phải verify surface của `google-genai==0.8.0`; retry phải viết lại bằng `asyncio.sleep` → 2 nhánh retry dễ lệch | |
| Nâng SDK lên 1.6x | function-calling chín hơn | đụng thứ vừa được đo kỹ (gate schema, `finish_reason.value == 2`) — rủi ro lớn nhất, mà D3 đã bỏ function-calling nên không đổi lại được gì | |

Traffic nội bộ vài chục câu/ngày thì thread pool mặc định (~32) dư sức.

**Singleton bắt buộc.** `AnalyzerService.__init__` tạo `GeminiClient()` mỗi lần khởi tạo service
(`analyzer.py:267`) — vô hại với script chạy một lần. Nhưng route dùng `Depends(...)` chạy **mỗi
request**; bắt chước pattern đó sẽ dựng một `genai.Client` mới cho từng câu hỏi = connection pool mới
+ re-auth Vertex mỗi lần. Client cho chat phải là module-level singleton (hoặc `app.state`).

### D7. Retrieval helper: mở rộng `InsightRepository`, xếp hạng dùng lại `score_for_role`

`list_paginated` thiếu `topics` và cửa sổ thời gian. Thêm **method riêng**
`list_for_chat(published_since, topics=None, roles=None, keyword=None)` thay vì nhồi thêm tham số vào
`list_paginated` (hàm đó phục vụ UI, thêm param là thêm bề mặt hồi quy cho dashboard). Bắt buộc giữ
`status == "published" AND is_primary == True` — đếm/lọc lệch điều kiện này là lỗi đã có tiền lệ và có
test canh (`tests/test_insight_count_queries.py`).

**Xếp hạng hai tầng: độ LIÊN QUAN tới câu hỏi trước, rồi mới tới độ QUAN TRỌNG chung.**

```
key = ( số từ khoá câu hỏi khớp trong title/signal/so_what/topics/roles ,
        score_for_role(...)  ← gọi thẳng của delivery, KHÔNG viết lại )
```

Tầng độ-liên-quan là bắt buộc kể từ khi có trần top-K (xem D3): nếu thiếu, tin đúng chủ đề nhưng
urgency thấp bị cắt sạch (recall 42%). Câu hỏi chung chung không có từ khoá đặc trưng → tầng một hoà
0 → tự động rơi về xếp theo độ quan trọng, đúng hành vi cũ.

Ngưỡng độ dài từ khoá là **2 ký tự**, không phải 3: tiếng Việt đơn âm nên lọc ở 3 làm "mã nguồn mở"
rụng còn `['nguồn']`, mất sạch "mã", "mở", "dữ", "AI". Nhiễu do `_STOPWORDS` gánh, không giao cho độ
dài. (Đo: sửa ngưỡng đưa riêng ca "mã nguồn mở" từ 94% → 100%, tổng recall giữ nguyên 91%.)

Tầng độ-quan-trọng dùng lại `score_for_role()` vì số liệu:

| Vai trò | Entry | `high` | |
|---|---:|---:|---|
| Security | 64 | 42 | 66% — ngập |
| AI Engineer | 126 | 25 | |
| Tech Lead | 128 | 12 | |
| Dev | 97 | 4 | |
| Data Engineer | 28 | 3 | |
| Data Scientist | 49 | **0** | đói tuyệt đối |
| Toàn công ty | 4 | 0 | |
| Data Analyst · Người dùng phổ thông | **0** | 0 | không xuất hiện lần nào |

Với Data Scientist thì **mọi tin đều `medium`** → xếp hạng chỉ dựa role urgency sẽ suy biến thành
ngẫu nhiên. Tuple đa tiêu chí của `score_for_role` (urgency → `impact_label` → có
`practical_indicators` → `actionability_score` → Strategic → `trust_score` → mới hơn) đã giải đúng bài
này ở delivery. Đây cũng là bài học 21/07: **xếp hạng, không lọc ngưỡng** — lọc ngưỡng vừa làm ngập
Security vừa bỏ đói Data Scientist.

Hai vai trò có **0 dữ liệu** → chat SHALL nói rõ "chưa có tin nào cho vai trò này", không im lặng.

**Topic có 7 giá trị ngoài tập đóng**: `IoT & thiết bị` (×6) và `Agent / AI / Data Science` (×1) —
model mượn chữ từ phần bối cảnh 4 trụ cột của `GATE_PROMPT` (sửa 21/07) sang phần phân loại;
`analyzer.py` không validate `topics` (vì `analyze()` cố ý không bật `response_schema`). Index chở
topic nguyên trạng nên 7 tin này vẫn hiện; chỉ cần không dùng topic làm **filter cứng**.

### D8. Widget: component React thuần, mount ở `Layout.tsx`

`ChatWidget` panel nổi ~380px góc phải, CSS Modules như phần còn lại, TanStack Query mutation. Context
chip lấy insight đang mở từ route param `/insights/:id`. Không streaming v1 — 1 lần gọi ~3-6s, spinner
là đủ. History giữ trong state component (stateless phía server), cap 10 lượt gửi kèm.

## Risks / Trade-offs

- [Model bịa nội dung dù không bịa được citation] → grounding rules trong system prompt + marker `[n]`
  bắt buộc cho mọi khẳng định + fail-closed khi không có marker nào (D4). Vẫn cần rà tay ở task 5.2.
- [Corpus phình vượt sức chứa prompt] → `chat_window_days` là van xả, hạ dần 0 → 90 → 30 (D3); mốc
  cần xem lại là khi vượt ~1250 tin.
- [Thread pool cạn nếu chat bị spam] → quota 200 lượt/ngày là hàng rào; dashboard không auth nên đây
  là hàng rào duy nhất (D5).
- [Va chạm RPM với batch analysis lúc 13h] → chấp nhận; analysis có retry backoff (D5).
- [Mode B mất bài gốc sau tombstone] → fallback insight-fields + nói rõ, từ ~11/2026 (D2).
- [Widget che nội dung trên màn hình hẹp] → panel toggle, không auto-mở, responsive full-height mobile.
- [Câu hỏi bằng tiếng Anh trên index tiếng Việt] → index chở cả `title` (thường tiếng Anh) lẫn
  `signal` (tiếng Việt) nên khớp được hai chiều; không có ILIKE cứng nào để trượt.

## Open Questions

- **Streaming — hoãn có chủ đích, xét lại sau khi hạ được thinking.** Nhìn thì streaming là cách hiển
  nhiên để chữa độ trễ 5-22s, nhưng thinking tokens sinh **trước** token hiển thị đầu tiên: ở top-60
  vẫn còn 2.534 token thinking, chiếm gần hết 15s. Bật streaming bây giờ chỉ khiến người dùng nhìn
  panel trống lâu hơn thay vì nhìn spinner. Chỉ đáng làm sau khi `thinking_budget` hạ được thinking.
- **Nâng `google-genai` lên 1.x để dùng `thinking_budget`** — thinking chiếm ~70% chi phí còn lại
  ($0,0063 trong $0,0090 ở top-60). Là non-goal của change này (rủi ro cho pipeline analysis); tách
  thành change riêng, lấy benchmark gate 54 doc làm lưới hồi quy.
- **Recall 91% có đủ chưa?** 13/151 tin liên quan vẫn rơi ngoài top-60 (kém nhất: AWS 81%). Nới K lên
  80-100 sẽ kéo lên nhưng ăn vào phần tiết kiệm. Chưa có người dùng thật phàn nàn nên giữ 60.

- Có cần log **nội dung** câu hỏi để đánh giá chất lượng (M9 Feedback)? v1 chỉ log metadata
  (mode, model_calls, citations_count, latency) — không lưu câu hỏi lẫn câu trả lời.
- `chat_window_days` mặc định 0 (cả corpus) có nên đổi khi corpus qua ~600 tin, hay đợi tới lúc chi
  phí thực đo vượt ngưỡng chịu được?
- 7 giá trị topic ngoài tập đóng có nên dọn bằng một script chuẩn hoá, hay để tự rụng theo retention?
  (Ngoài phạm vi change này.)
