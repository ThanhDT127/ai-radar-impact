# Proposal: chat-chunk-retrieval

**Phase áp dụng:** Phase 2 (M8 Chatbot) — **sau** `chat-context-depth`. Ưu tiên thấp, xem "Điều kiện mở".

## Why

Tầng truy hồi toàn cục **không nhìn thấy thân bài**. `build_embedding_text` embed
`title + signal + so_what + summary_short + topics` — tức là **bản phân tích do Gemini viết ra**, không
phải bài viết. `raw_documents.normalized_content` (tới 8.000 ký tự) không được embed, không được chunk,
không có mặt trong bất kỳ tín hiệu xếp hạng nào.

Đo trên 10 bài có raw content trong fixture (28/07/2026): biểu diễn truy hồi phủ **4,0%** từ vựng thân bài
(vector) và **4,1%** (lexical). Nội dung mất đi là loại đặc trưng nhất — `CVE-2026-9770`, `squashfs`,
`Annex III`, `chunk 512 / overlap 50`, `@asyncapi/generator@3.3.1`, mốc `October`.

Hệ quả **còn lại sau `chat-context-depth`**: change đó rót đầy đủ thân bài cho 3 ô sâu, nên câu hỏi chi
tiết *về bài đã xếp hạng cao* trả lời được. Cái nó **không** chữa là **khám phá bằng chi tiết** — câu hỏi
mà từ khoá định danh chỉ tồn tại trong thân bài, nên `_rank` không có tín hiệu nào để đưa bài đó lên:

> *"Tin nào nhắc tới CVE‑2026‑9770?"* · *"Bài nào dùng squashfs để phân tích firmware?"*

⚠️ **Chế độ hỏng này CHƯA được đo.** 6/6 câu hỏi chi tiết trong spike vẫn truy hồi đúng ở **hạng 1**, vì
từ khoá chủ đề (`AsyncAPI`, `EU AI Act`, `Windows Server 2022`) **có** trong phần phân tích. Con số 4%
là điều kiện cần, chưa phải bằng chứng. Task 0 của change này là **đo trước, quyết sau**.

## What Changes

- **Bảng `document_chunks`**: `raw_document_id`, `insight_id`, `ordinal`, `content`, `embedding vector(768)`,
  index HNSW cosine. Chunk theo cửa sổ có overlap, cắt ở ranh giới câu.
- **Tín hiệu thứ ba trong RRF**: cạnh lexical và vector‑insight, thêm **vector‑chunk**. Một insight nhận
  thứ hạng của **chunk tốt nhất** thuộc về nó. Công thức thành `1/(60+r_lex) + 1/(60+r_vec) + 1/(60+r_chunk)`.
- **Citation vẫn ở mức insight.** Chunk **không bao giờ** là đích của marker `[n]`. Chunk phục vụ *xếp hạng*;
  nội dung phục vụ câu trả lời vẫn đến từ ô sâu của `chat-context-depth`. Giữ trọn D4.
- **Lọc thô đẩy xuống SQL.** ~700–1.000 chunk × 768 chiều ≈ 3MB/lượt — không kéo hết về Python được nữa.
  Dùng `ORDER BY embedding <=> :q LIMIT n` trên index HNSW (đã dựng sẵn ở migration 012).
- **Vòng đời**: sinh chunk + embedding khi ingest/analyze; script backfill idempotent; purge theo
  `retention_months` cùng nhịp với `normalized_content`.

## Capabilities

### Modified Capabilities
- `chat-qa-service`: xếp hạng toàn cục SHALL nhận thêm tín hiệu tương đồng ở mức đoạn văn bản gốc, trong
  khi định danh trích dẫn SHALL giữ ở mức insight.

## Non-goals

- **Không** đổi granularity của citation — chunk không thành nguồn trích dẫn.
- **Không** rerank cross‑encoder (vẫn để dành, cùng chỗ với `rank-eol-khai-tu`).
- **Không** đụng ô sâu / working set của `chat-context-depth` — change này chỉ thêm tín hiệu xếp hạng.
- **Không** chunk phần phân tích insight (nó vốn ngắn, embed cả cục là đúng).

## Điều kiện mở (gate trước khi implement)

Change này **chỉ đáng làm nếu** Task 0 đo được chế độ hỏng thật:
≥ 30% câu "khám phá bằng chi tiết" có bài đúng nằm **ngoài top‑5** với `_rank` hiện tại.
Dưới ngưỡng đó ⇒ đóng change, ghi lý do — cái giá kiến trúc (mục Impact) quá đắt so với phần thắng.

## Dependencies

- **`chat-context-depth` — cứng, land trước.** Nó cung cấp ô sâu; không có ô sâu thì tìm được bài cũng chỉ
  đọc được 115 token, tức là chữa nửa vời.
- `chat-hybrid-retrieval` (archive): RRF và pgvector đã có; change này thêm số hạng thứ ba.

## Impact

- **DB migration**: bảng `document_chunks` + index HNSW. Dung lượng vector tăng ~5–6× so với hiện tại.
- **⚠️ Phá tính thuần của `_rank`.** Đây là cái giá lớn nhất: `chat_rank_harness` chạy **miễn phí, offline,
  trong `pytest` mặc định** đúng vì `_rank` là hàm thuần trên fixture. Đẩy lọc thô xuống SQL nghĩa là hoặc
  fixture phải mang cả chunk + kết quả truy vấn đông lạnh, hoặc harness phải cần DB. **Phải giải quyết
  trong `design.md` trước khi viết dòng code đầu tiên** — mất bộ đo đó là mất lưới duy nhất bắt hồi quy
  xếp hạng.
- Ingest chậm hơn (thêm lượt embed/chunk); không nằm trên đường phục vụ người dùng.
