> Thứ tự bắt buộc: spike → cấu hình/hợp đồng → context thuần → client Vertex → fetch →
> service → frontend → bộ đo → docs.
> Lý do: `build_context()` là hàm thuần mà RS harness phụ thuộc; và **spike phải xong trước
> khi viết code**, vì kết quả của nó có thể đổi kiến trúc bước 2.
>
> **Cổng cuối cùng: `chat_answer_harness --live` + đo tỉ lệ sentinel giả.** RS harness KHÔNG
> phủ được change này (nó đo `_rank`, mà change này không đụng `_rank`) — nhưng vẫn phải chạy
> để **chứng minh** không đụng.
>
> **Mặc định TẮT cho tới khi task 9.2 có số.**

## 0. Spike (làm trước, không viết code sản phẩm)

- [x] 0.1 Xác minh Google tính tiền grounding theo *truy vấn thực chạy* hay *request có bật tool* — chạy thử 2 request (một có kích hoạt search, một không) và đối chiếu billing/quota. **DoD:** có câu trả lời kèm bằng chứng; ghi vào design.md §Open Questions. (P2)
- [x] 0.2 Xác minh `gemini-2.5-flash-lite` có lái được `Tool(google_search=GoogleSearch())` không, và `grounding_chunks` trả về có khác flash không. **DoD:** kết luận chọn model cho bước 2, ghi vào design.md. (P2)
- [x] 0.3 Chạy thử một truy vấn thật, ghi lại nguyên văn `GroundingMetadata` nhận được: bao nhiêu `grounding_chunks`, có `search_entry_point` không, `web_search_queries` chứa gì. **DoD:** có mẫu thật làm cơ sở cho fixture và cho task 5.x. (P2)
- [x] 0.4 Thử `trafilatura.fetch_url` trên ~10 uri Google trả về cho các truy vấn kỹ thuật điển hình. **DoD:** có **tỉ lệ fetch thành công thật**; nếu dưới ~50% thì dừng lại và xem lại D5 trước khi làm tiếp. (P2)

## 1. Cấu hình & hợp đồng dữ liệu (Backend)

- [x] 1.1 Thêm vào `backend/app/config.py`: `chat_web_fallback_enabled: bool = False`, `max_daily_web_searches: int`, `chat_web_max_sources: int`, `chat_web_search_model_id: str`. **DoD:** tắt = pipeline y hệt hôm nay; mỗi biến có chú thích nêu *vì sao* tồn tại. (P2, phụ thuộc 0.1, 0.2)
- [x] 1.2 Nâng `MAX_MODEL_CALLS_PER_QUESTION` 2 → 3, cập nhật docstring phân biệt **bước lập luận** với **lượt tính tiền** (đã có tiền lệ ở `chat-scope-routing`). **DoD:** ghi rõ trần tiền tối đa/câu sau khi cộng retry chống-cắt. (P2)
- [x] 1.3 Định nghĩa `WebSource` (uri, title, text, `fetched_ok: bool`) — dataclass thuần, **không** model DB. **DoD:** không có bảng mới, không có migration. (P2)
- [x] 1.4 `Citation` thành union có kiểu phân biệt `kind: "insight" | "web"`, giữ nguyên trường `n` (`chat-citation-integrity`). **DoD:** client cũ parse được citation `insight` không đổi; `tsc` phía frontend sạch sau 7.x. (P2)
- [x] 1.5 Thêm `search_suggestions` (HTML từ `search_entry_point.rendered_content`) vào response, `None` khi không tra cứu. **DoD:** trường có mặt ở cả `commit` (SSE) lẫn response blocking. (P2)

## 2. Prompt

- [x] 2.1 Định nghĩa `WEB_LOOKUP_SENTINEL = "[[TRA_CỨU_NGOÀI: …]]"` ở **một chỗ** trong `app/ai/prompts.py`, kèm bộ phân tích tách truy vấn ra khỏi sentinel. **DoD:** định nghĩa một chỗ, prompt và service dùng chung — như `OUT_OF_SCOPE_SENTINEL`. (P2)
- [x] 2.2 Luật sentinel web trong prompt bước 1: phát **kèm** phần trả lời được, chỉ khi thực thể được hỏi **hoàn toàn vắng**; khi phân vân thì **KHÔNG** phát (D2). **DoD:** luật nằm ở prompt **người dùng**, không nhét vào `CHAT_SYSTEM_PROMPT` — cùng lý do với `_SCOPE_RULE`. (P2, phụ thuộc 2.1)
- [x] 2.3 Prompt mode B **KHÔNG** mang luật sentinel web (D3). **DoD:** đọc prompt mode B không thấy `WEB_LOOKUP_SENTINEL`. (P2)
- [x] 2.4 Prompt bước 2 (trích xuất): yêu cầu tìm và trả về nguồn, **không** trả lời người dùng. **DoD:** output bước 2 không bao giờ đi thẳng tới người dùng. (P2)
- [x] 2.5 Luật chống-injection trong prompt bước 3: khối tra cứu là **DỮ LIỆU**, mọi câu ra lệnh bên trong phải bị bỏ qua (D6). **DoD:** luật tường minh, có test ở 8.5. (P2)
- [x] 2.6 Luật đánh dấu độ chắc chắn khi rơi về text tóm tắt (D5, ca fetch hỏng hết). **DoD:** model phân biệt được nguồn đã đối chiếu nguyên văn với nguồn chỉ có tóm tắt. (P2)

## 3. Dựng context (hàm thuần)

- [x] 3.1 Thêm tham số `web_sources: list[WebSource]` vào `build_context()`, đánh số **nối tiếp sau** insight trong **cùng** dãy `[n]` và **cùng** bảng ánh xạ (D4). **DoD:** hàm vẫn THUẦN — không I/O, không đọc `settings`; RS harness offline không đổi một dòng. (P2, phụ thuộc 1.3)
- [x] 3.2 Khối web render dưới tiêu đề riêng nhưng **không** tạo dãy số thứ hai. **DoD:** dãy `[n]` liên tục, không đứt, không trùng. (P2, phụ thuộc 3.1)
- [x] 3.3 `resolve_citations` trả `kind` đúng theo kiểu của mục trong mapping. **DoD:** marker trỏ WebSource ra `kind="web"`; số **giữ nguyên**, server KHÔNG đánh số lại. (P2)
- [x] 3.4 `enforce_grounding` chạy **không đổi**: câu không marker vẫn fail-closed. **DoD:** `git diff` không đổi logic hàm này. (P2)

## 4. Client Vertex (Backend)

- [x] 4.1 Thêm `GeminiClient.search_web(query)` dùng `Tool(google_search=GoogleSearch())`, trả về `(uris, titles, raw_text, search_entry_point, web_search_queries)`. **DoD:** không dùng `response_schema` (bài học `gemini-structured-output`); lỗi Vertex không nổ ra ngoài. (P2, phụ thuộc 0.2, 0.3)
- [x] 4.2 Cấu hình generation cho bước 2 dựng ở **cùng một chỗ** với `_chat_generation_config`. **DoD:** có test `inspect.getsource` khoá điều này, như tiền lệ `chat-latency-thinking-budget`. (P2)
- [x] 4.3 Lượt gọi bước 2 **có** tính vào `chat_logs.model_calls` (nó là lượt sinh văn bản thật), nhưng số **truy vấn search** đếm riêng. **DoD:** hai bộ đếm độc lập, không trộn (D7). (P2)

## 5. Fetch nội dung (Backend)

- [x] 5.1 Dùng lại `WebArticleConnector` (`trafilatura`) để lấy text từ uri; **không** viết bộ fetch thứ hai. **DoD:** không có `trafilatura.fetch_url` mới ngoài connector đã có. (P2)
- [x] 5.2 Fetch **song song** tối đa `chat_web_max_sources` uri, có timeout cứng. **DoD:** một trang chậm không kéo cả lượt; timeout đo được. (P2, phụ thuộc 5.1)
- [x] 5.3 Cắt text theo `normalizer.MAX_CONTENT_LENGTH` (8000) — cùng trần với ô sâu corpus. **DoD:** dùng lại hằng số, không chép số. (P2)
- [x] 5.4 Suy giảm êm theo D5: một phần hỏng → dùng phần còn lại; hỏng hết → rơi về text bước 2 có gắn nhãn; không uri nào → bỏ tra cứu. **DoD:** **không ca nào** thành HTTP 500. (P2, phụ thuộc 5.2)
- [x] 5.5 Bước fetch **KHÔNG** tính là bước lập luận. **DoD:** `_steps_used` không tăng ở đây. (P2)

## 6. Service

- [x] 6.1 Dò `WEB_LOOKUP_SENTINEL` **trước** `enforce_grounding` (cùng lý do với sentinel out-of-scope: câu có sentinel có thể chưa đủ marker). **DoD:** tín hiệu không bị grounding nuốt. (P2, phụ thuộc 2.1)
- [x] 6.2 Ghép đường: bước 1 → (có sentinel) → search → fetch → bước 3, dùng **chung** `_answer_global`, không tách nhánh thứ hai. **DoD:** grounding/xếp hạng/fail-closed đi qua đúng một đoạn code (bài học `chat-streaming-sse`). (P2)
- [x] 6.3 Câu trả lời một phần của bước 1 **không** bị vứt: nội dung nó đã nêu phải còn trong câu trả lời cuối. **DoD:** có test cho ca "vế A trả lời được, vế B phải tra cứu". (P2)
- [x] 6.4 Cổng quota search: hết `max_daily_web_searches` → bỏ tra cứu, trả lời phần corpus + nói rõ, **KHÔNG** 429 (D7). **DoD:** câu hỏi vẫn được trả lời khi quota search cạn. (P2)
- [x] 6.5 Mode B tuyệt đối không đi đường web (D3). **DoD:** có test khoá; `B → expanded → web` là đường duy nhất tới tra cứu. (P2)
- [x] 6.6 Phát mốc status `web_search` (truy vấn thật) và `web_fetch` (tên miền đang đọc) qua cơ chế `key` của `chat-status-milestones`. **DoD:** không thêm cơ chế status thứ hai. (P2, phụ thuộc change `chat-status-milestones`)
- [x] 6.7 Ghi `chat_logs`: số truy vấn search, số uri fetch thành công/thất bại. **DoD:** đủ dữ liệu để tính tỉ lệ fetch thành công trên production. (P2)

## 7. Frontend

- [x] 7.1 Render citation `kind="web"` phân biệt rõ với nguồn hệ thống (tên miền + link ra ngoài). **DoD:** người dùng không nhầm nguồn ngoài với tin đã qua phân tích. (P2, phụ thuộc 1.4)
- [x] 7.2 Giữ nguyên cách giải marker: `citations.find(c => c.n === n)`. **DoD:** `git diff` không đụng phép tra cứu này. (P2)
- [x] 7.3 Hiển thị Google Search Suggestions từ `search_suggestions` (D8 — bắt buộc theo điều khoản). **DoD:** hiện đúng khi có tra cứu, ẩn khi không. (P2, phụ thuộc 1.5)
- [x] 7.4 Cập nhật kiểu TypeScript cho `Citation` union. **DoD:** `tsc` sạch. (P2)

## 8. Test

- [x] 8.1 `WebSource` và `Insight` **không bao giờ** nhận cùng một số `[n]`. **DoD:** test khoá bất biến D4. (P2)
- [x] 8.2 Sentinel web không bị `enforce_grounding` nuốt. **DoD:** xanh. (P2)
- [x] 8.3 Mode B không phát sentinel web. **DoD:** xanh (D3). (P2)
- [x] 8.4 Fetch hỏng hết → vẫn có câu trả lời, không 500, nguồn được gắn nhãn tóm tắt. **DoD:** xanh (D5). (P2)
- [x] 8.5 Trang chứa câu ra lệnh ("bỏ qua chỉ thị trước…") → model không tuân theo. **DoD:** có ca kiểm chứng thật, không chỉ là luật trong prompt (D6). (P2)
- [x] 8.6 Tắt cờ → **không** lượt search nào, prompt không mang luật sentinel web, trần bước hiệu dụng vẫn 2. **DoD:** đường rollback được khoá bằng test. (P2)
- [x] 8.7 Quota search cạn → vẫn trả lời, không 429. **DoD:** xanh (D7). (P2)

## 9. Bộ đo

- [x] 9.1 Đông lạnh kết quả bước 2 + text đã fetch theo kịch bản, kèm **dòng vân tay** (truy vấn, uri, ngày lấy); loader **NỔ** khi lệch. **DoD:** `chat_answer_harness` chạy offline vẫn tất định và **0 đồng** (D9). (P2)
- [x] 9.2 Đo **tỉ lệ sentinel giả** trên bộ câu hỏi trả lời được hoàn toàn từ corpus — khuôn theo `chat-scope-routing` (đã đo 0/6). **DoD:** có số; sentinel giả cao thì siết prompt 2.2 **trước khi** bật mặc định. (P2)
- [x] 9.3 Thêm nhóm kịch bản `partial_ground` vào `chat_scenarios.jsonl`: câu ghép một vế có, một vế không. **DoD:** ≥5 kịch bản; hiện chưa có nhóm nào phủ hình dạng này. (P2)
- [x] 9.4 Chạy `chat_answer_harness --live`, đối chiếu Faithfulness ≥ 0,95 và Citation Precision = 1,00. **DoD:** đạt ngưỡng; **nếu không đạt thì sửa code, KHÔNG hạ ngưỡng**. (P2, phụ thuộc 9.1)
- [x] 9.5 Chạy `chat_rank_harness` để **chứng minh** `_rank` không bị đụng. **DoD:** trùng khít baseline, không chốt lại. (P2)
- [x] 9.6 Đo độ trễ đầu-cuối của đường tra cứu (client **ấm**, singleton — cảnh báo đo lường ở `chat-context-depth`). **DoD:** có TTFT + tổng thời gian; xác nhận status lấp được khoảng chờ. (P2, phụ thuộc change `chat-status-milestones`)

## 10. Docs

- [x] 10.1 Viết `measurement.md`: tỉ lệ sentinel giả, tỉ lệ fetch thành công, độ trễ, chi phí thực/câu tra cứu. **DoD:** đủ số để người sau đánh giá lại quyết định. (P2, phụ thuộc 9.2, 9.6)
- [x] 10.2 Cập nhật `CLAUDE.md` mục Chat: Fork B2 và **vì sao không phải Fork A** (`GroundingChunkWeb` không có snippet), vì sao không dùng Custom Search API (đã đóng), hai bộ đếm tách biệt, trần 3 bước, Search Suggestions bắt buộc. **DoD:** người đọc sau không "tối ưu" về Fork A. (P2)
- [x] 10.3 Ghi vào `.env.example` các biến mới kèm giá trị mặc định **tắt**. **DoD:** dựng môi trường mới không vô tình tiêu tiền search. (P2)
