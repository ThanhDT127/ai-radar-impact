## Why

Grounding fail-closed hiện là **tất cả hoặc không gì**. Đo thật 03/08/2026 trên câu *"thông số
model này so với Gemini Embedding 2 khác nhau như nào"* khi đang đọc bài NVIDIA Nemotron 3
Embed: bot từ chối **toàn bộ**, dù corpus có đủ vế Nemotron (8B/1B, ngữ cảnh 32k, NVFP4,
hạng #1 RTEB, kèm `risks` vendor-lock). Hai khiếm khuyết tách bạch:

1. **Từ chối cả vế trả lời được.** Câu hỏi ghép hai vế, thiếu một vế thì mất luôn vế kia.
2. **Corpus là DÒNG TIN, không phải cơ sở dữ liệu thông số.** Câu "X vs Y" chỉ trả lời được
   khi cả hai có bài trong cửa sổ — xác suất thấp theo cấu trúc, không phải do xếp hạng kém.

Luật số 1 của `CHAT_SYSTEM_PROMPT` (*"tuyệt đối không dùng kiến thức riêng"*) vẫn **đúng** —
lý do là *model không có nguồn để người dùng kiểm chứng*. Cách chữa phải là **nới cái gì được
coi là có căn cứ**, không phải bỏ căn cứ.

⚠️ Bản trước của dòng này ghi *"tên sản phẩm nhiều khả năng không tồn tại"*. **Sai** — spike
0.4b lấy về tài liệu chính thức `Gemini Embedding 2 | Gemini Enterprise Agent Platform`. Người
dùng hỏi một thứ **có thật, tài liệu công khai đầy đủ**, và bot vẫn im. Điều đó làm ca hỏng
này *nặng hơn*, không nhẹ đi.

## What Changes

- Model phát sentinel **mang tham số** `[[TRA_CỨU_NGOÀI: <truy vấn>]]` **kèm theo** phần trả
  lời được từ corpus — tín hiệu là byproduct của chính lượt trả lời, không phải classifier.
- Bước tra cứu dùng **Grounding with Google Search** của Vertex, nhưng **chỉ lấy `uri`**; text
  lấy bằng `trafilatura` qua `WebArticleConnector` đã có sẵn.
- Mỗi trang tải được thành một `WebSource` được **server đánh số trong cùng dãy `[n]`** và cùng
  một bảng ánh xạ với insight. Prompt vẫn không chứa uri/UUID.
- `MAX_MODEL_CALLS_PER_QUESTION` **2 → 3**; bước fetch không tính là bước.
- Bộ đếm ngày riêng `max_daily_web_searches`; mặc định **tắt** toàn tính năng.
- Widget hiển thị nguồn web phân biệt được với nguồn hệ thống, kèm Google Search Suggestions
  theo yêu cầu bắt buộc của Google.

## Capabilities

### New Capabilities
- `chat-web-fallback`: tra cứu ngoài khi corpus thiếu dữ kiện, giữ nguyên mô hình trích dẫn.

### Modified Capabilities
- `chat-qa-service`: trả lời **một phần** thay vì từ chối toàn bộ; trần bước 2 → 3.
- `chat-web-widget`: render nguồn web + Search Suggestions.
- `chat-answer-eval-harness`: đông lạnh kết quả tra cứu để harness vẫn offline/tất định.

## Non-goals

- **KHÔNG** cho model dùng kiến thức nền không có nguồn (phương án ② đã cân nhắc và loại): nó
  phá `Faithfulness` theo định nghĩa và tạo ra lời bịa có kèm nguồn.
- **KHÔNG** để model tự trả lời khi bật tool (Fork A). `GroundingChunkWeb` chỉ có
  `domain/title/uri` — **không có snippet** (xác minh trên SDK 1.75.0) ⇒ context của ta không
  còn đầy đủ, `grounding_supports` thành hệ trích dẫn thứ hai chạy song song với `[n]`, đúng
  cái bẫy `chat-citation-integrity` đã trả giá.
- **KHÔNG** dùng Custom Search JSON API để tự gọi search: **đã đóng với khách mới từ 2025**,
  khách cũ dừng 01/01/2027.
- **KHÔNG** gộp bước 1 và 2 (bật tool ngay lượt đầu) ở v1 — chưa xác minh Google tính tiền
  theo *truy vấn thực chạy* hay *request có bật tool*. Ghi thành spike trong design.
- **KHÔNG** đưa nội dung web vào corpus/DB. Nó sống đúng một lượt hỏi, không thành `Insight`.
- **KHÔNG** đụng `_rank`, RRF, `_relevance`, embedding ⇒ không chốt lại baseline RS.

## Phase

**Phase 2** — M8 (Chat Q&A) + M6 (Dashboard).

⚠️ **Sửa 03/08 khi implement**: bản đầu ghi *"không migration DB"*. Sai — `max_daily_web_searches`
là trần **tiền**, mà trần tiền phải sống sót qua restart; bộ đếm trong bộ nhớ biến một vòng lặp
restart thành một vòng lặp tiêu tiền không giới hạn. Nên có **migration 015**: một cột nullable
`chat_logs.web_searches`, đúng khuôn 013 và đúng nguyên tắc sẵn có *"bảng log cũng chính là
counter"*. Nội dung web vẫn **không** được ghi xuống — nó vẫn chỉ sống trong một lượt hỏi.

## Dependency

Phụ thuộc **`chat-status-milestones`** (land trước): tính năng này thêm 1 bước model + fetch
mạng vào TTFT, mà bài học `chat-streaming-sse` đã chốt *status mới là thứ che độ trễ*.
