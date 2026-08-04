## Context

Chat mất 14,6–29,1s/câu. `chat-streaming-sse` (27/07) đã che phần **cảm nhận** bằng hai sự
kiện `status` ở giây ~0,7/~1,0, nhưng số đo của chính change đó cũng nói thẳng: TTFT thật vẫn
**8,0–36,7s**, và toàn bộ khoảng đó là **thinking — chưa có token nào để stream**. Nghĩa là
streaming đã dùng hết dư địa của nó; muốn nhanh thật thì phải giảm chính phần thinking.

**Số đo 27/07/2026** (`gemini-2.5-flash`, Vertex us-central1, prompt chat thật ~6,5k token):

| | thời gian | thinking | ra |
|---|---|---|---|
| "lỗ hổng nào cần vá gấp" | 14,9s | 2.752 | 233 |
| "mô hình mã nguồn mở nào mới" | 17,7s | 2.733 | 269 |
| "tuần này có tin gì quan trọng" | 14,6s | 1.877 | 282 |
| prompt tầm thường (534 vào / 10 ra) | **10,3s** | 1.416 | 10 |

Dòng cuối là bằng chứng quyết định: độ trễ **không** tỉ lệ với kích thước ngữ cảnh. Vì vậy
đường "cắt top-K cho prompt nhỏ lại" là sai — đo trực tiếp: K 60 → 10 giảm token vào 76% mà
chỉ đưa 17,4s xuống 11,6s.

Chi phí này **vô hình** ở bản SDK đang pin: `google-genai==0.8.0` trả `thoughts_token_count`
rỗng, nên `usage_metadata` nhìn như thể thinking = 0. Phải suy ra từ
`total_token_count − prompt − candidates`.

**Module ảnh hưởng:** M8 (Chatbot). **API endpoints:** không đổi. **Bảng DB:** chỉ thêm cột
log (tuỳ chọn). **AI/LLM:** cùng model, thêm `ThinkingConfig`.

## Goals / Non-Goals

**Goals:**
- Câu tra cứu thường **≤ 5s** đầu-cuối; câu tổng hợp kiểu "tin tuần này" **≤ 8s**.
- Giữ nguyên chất lượng: Faithfulness ≥ 0,95 và Citation Precision = 1,00 (cổng cứng của ④).
- Làm chi phí thinking **nhìn thấy được** để nó không âm thầm quay lại.

**Non-Goals:**
- Không cắt `CHAT_INDEX_TOP_K` (đo được là sai đường, và trả bằng recall).
- Không đụng `_rank`/retrieval/grounding/citation/scope/streaming.
- Không đổi `thinking_budget` của gate/analysis; không đổi model.

## Decisions

### D1 — Nâng `google-genai` lên 2.x thay vì tự gọi REST

`thinking_budget` là tham số của API, không phải tính năng SDK — về lý thuyết có thể gọi thẳng
REST để tránh nâng cấp. Bỏ, vì như thế là dựng một đường gọi model **thứ hai** song song với
SDK cho đúng một tham số, rồi phải tự lo retry/auth/streaming/parse cho nó. Nâng SDK là đường
thẳng; cái giá là **API surface dùng chung** (gate, analyze, chat, chat_stream, classify_intent,
embed) nên toàn bộ suite phải xanh lại — đó chính là việc của task 1.x.

`0.8.0 → 2.x` cũng trả lại `thoughts_token_count` thật, thứ mà bản cũ giấu.

### D2 — `thinking_budget = 256`, CHỈ cho chat, và là **hằng số cấu hình được**

Đo trên prompt chat thật: không đặt → 8,2s/1.023 thinking; **256 → 3,7s/253**; 0 → 1,8s;
1024 → 7,8s. Chọn **256** thay vì 0 (Hung chốt): 0 nhanh hơn 1,9s nhưng bỏ sạch biên suy luận,
mà câu tổng hợp nhiều tin là đúng loại câu cần nó nhất — và ngân sách thời gian tới 8s cho
nhóm đó thì không cần ép tới 0.

Cấu hình được (`CHAT_THINKING_BUDGET`) vì đây là **núm đánh đổi tốc độ ↔ chất lượng**, và luật
chỉnh nó đã định sẵn ở D5: gate đỏ thì nâng, không hạ ngưỡng.

*Đã cân nhắc:* budget động theo loại câu hỏi (0 cho câu thường, cao cho câu tổng hợp). Bỏ ở
v1 — nó cần một bộ phân loại "câu này có cần suy luận không", tức là thêm một chỗ đoán sai
được, để mua ~1,9s. Mở lại nếu 256 tỏ ra vừa chậm cho câu thường vừa thiếu cho câu tổng hợp.

### D3 — `chat()` và `chat_stream()` phải nhận CÙNG cấu hình

Hai lối ra dùng chung pipeline là bất biến đã ghi của `chat-streaming-sse`. Đặt thinking cho
mỗi `chat()` sẽ làm bản blocking và bản streaming trả lời **khác nhau** một cách im lặng — và
tệ hơn: eval harness ④ đi lối blocking, nên cổng chất lượng sẽ gác một cấu hình mà người dùng
thật không chạy. Cấu hình dựng ở **một chỗ** dùng chung cho cả hai.

### D4 — Embed câu hỏi ‖ truy vấn DB

`_embed_question` (~1,4s) và `list_for_chat` (~0,2s) hiện chạy tuần tự nhưng độc lập hoàn
toàn. `asyncio.gather` cắt ~0,2s. Nhỏ, nhưng ở ngân sách 5s thì 0,2s là 4%.

⚠️ Thứ tự **phải giữ**: cổng "câu hỏi rỗng từ khoá thì bỏ tầng vector" của ⑥ nằm trong
`_rank`, không nằm ở chỗ gọi embed — chạy song song không được phép biến nó thành "luôn embed
rồi mới xét", vì như thế là tiêu 1,4s cho câu mà kết quả sẽ bị vứt. Lượt embed cho câu rỗng từ
khoá phải **bỏ hẳn**, không phải bỏ kết quả.

### D5 — Cổng chất lượng quyết giá trị budget, không phải cảm nhận

`chat_answer_harness --live` chạy lại **toàn bộ** sau khi đổi: đổi ngân sách suy luận là đổi
câu trả lời, y như đổi context. Luật: Faith < 0,95 **hoặc** CitPrec < 1,00 ⇒ nâng 256 → 512 →
1024 cho tới khi xanh, **không hạ ngưỡng**. RS harness phải cho số **y hệt** — nó đo `_rank`
thuần, mà change này không đụng `_rank`; RS đổi số nghĩa là đã chạm nhầm chỗ.

### D6 — Ghi số token suy luận vào log

Chi phí này ẩn được 5 ngày chỉ vì SDK không phơi nó ra. Ghi `thoughts_token_count` vào
`chat_logs` (và log DEBUG) để lần sau nó là số đọc được, không phải thứ phải suy ra từ hiệu ba
con số. Thinking bị **tính tiền như output** ($2,50/1M) nên đây cũng là số liệu chi phí.

## Risks / Trade-offs

- **[Nâng SDK phá chỗ khác]** → API surface dùng chung; chạy full suite (313 test) + kiểm tay
  cả 6 điểm gọi model (gate, analyze, chat, chat_stream, classify_intent, embed) trước khi đo
  chất lượng. Rollback = trả lại pin cũ, `thinking_config` là phần duy nhất phải gỡ theo.
- **[Cắt thinking làm câu trả lời tệ đi một cách khó thấy]** → đúng loại hồi quy mà ④ sinh ra
  để bắt: LLM-judge chấm Faithfulness/Answer-Relevance, structural chấm Citation Precision.
  Không dựa vào mắt thường.
- **[256 vừa đủ hôm nay, thiếu khi corpus/prompt đổi]** → là hằng số cấu hình, và số đo được
  ghi lại kèm ngày để lần sau so được.
- **[Đo độ trễ trên máy local, mạng khác production]** → mọi số đều là round-trip tới Vertex
  us-central1 từ cùng một chỗ; so sánh **trước/sau trên cùng máy** mới có nghĩa, con số tuyệt
  đối thì không hứa cho môi trường khác.

## Migration Plan

1. Nâng `google-genai` trong `requirements.txt`, build lại image, chạy full suite → xanh.
2. Kiểm tay 6 điểm gọi model còn chạy đúng (đặc biệt `chat_stream` và `embed`).
3. Thêm `ThinkingConfig` dùng chung cho `chat()` + `chat_stream()`, `CHAT_THINKING_BUDGET=256`.
4. `gather` embed ‖ DB (giữ đúng luật bỏ embed cho câu rỗng từ khoá).
5. Log `thoughts_token_count`.
6. Đo lại độ trễ trước/sau trên cùng bộ câu; chạy `chat_answer_harness --live` (cổng cứng);
   chạy RS harness (phải không đổi).
7. Docs.

Rollback: hạ pin SDK + gỡ `thinking_config`; không có thay đổi dữ liệu nào cần hoàn tác ngoài
cột log (nullable).

## Open Questions

- **Có cần budget động theo loại câu hỏi không** — chỉ mở lại nếu số đo cho thấy 256 vừa chậm
  cho câu thường vừa thiếu cho câu tổng hợp (D2).
- **`thinking_level` của SDK 2.x** (tham số mới bên cạnh `thinking_budget`) có phải cách diễn
  đạt ổn định hơn không — xác minh khi đã có SDK trong tay, đừng đoán trước.
