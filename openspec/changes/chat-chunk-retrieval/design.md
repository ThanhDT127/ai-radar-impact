# Design: chat-chunk-retrieval

**Module:** M8 (Chatbot/Search), chạm M2/M3 (ingest sinh chunk). **Model:**
`text-multilingual-embedding-002` @768 — cùng model, cùng chiều với `insights.embedding`; **không** trộn
hai họ vector. **Grounding:** không đổi — D4 nguyên vẹn, chunk không phải đích citation.

## Ranh giới cốt lõi: chunk XẾP HẠNG, insight TRÍCH DẪN

```
        chunk (mới)                          insight (giữ nguyên)
   ┌──────────────────────┐            ┌────────────────────────────┐
   │ tìm ra BÀI NÀO liên  │  ──rank──▶ │ mang NỘI DUNG vào context  │
   │ quan (r_chunk)       │            │ + là đích của marker [n]   │
   └──────────────────────┘            └────────────────────────────┘
         không bao giờ xuất hiện trong prompt dưới dạng nguồn riêng
```

Lý do: `chat-citation-integrity` đã trả giá một lần cho việc có **hai hệ quy chiếu** cho `n`. Cho chunk
thành nguồn trích dẫn là dựng lại đúng cái bẫy đó ở quy mô lớn hơn (một insight có 5 chunk ⇒ 5 số cho
cùng một bài, và câu trả lời trích 3 số trỏ cùng một nguồn).

## Quyết định thiết kế

### D1 — Insight nhận thứ hạng của chunk TỐT NHẤT, không phải trung bình
`r_chunk(insight) = min(rank của mọi chunk thuộc insight)`. Trung bình sẽ phạt bài dài (nhiều chunk lạc
đề) — đúng loại thiên lệch ngầm mà `_vector_ranks` đã phải tránh với tin thiếu embedding.

### D2 — Insight không có chunk mượn thứ hạng vector của chính nó
Cùng luật với tin thiếu embedding hôm nay: `r_chunk = None → dùng r_vec`. **Không** bỏ số hạng (phạt ngầm
một nửa điểm) và **không** cho cosine 0 (biến "chưa biết" thành "chắc chắn không liên quan"). Trong cửa
sổ backfill, bài chưa chunk vẫn cạnh tranh đầy đủ.

### D3 — Chunking: cửa sổ có overlap, cắt ở ranh giới câu
- kích thước ~400–600 token, overlap ~15%; cắt ưu tiên tại `\n\n` rồi `.` — không cắt giữa câu.
- `normalized_content` đã bị trần 8.000 ký tự từ ingest ⇒ tối đa ~6 chunk/bài, ~1.000 chunk cho corpus 179.
- **Hằng số chunk là một phần của hợp đồng embedding**: đổi kích thước/overlap ⇒ phải backfill lại toàn bộ,
  cùng luật với `build_embedding_text` (`embed_insights --redo`).

### D4 — ⚠️ Giữ `chat_rank_harness` miễn phí và offline — giải quyết TRƯỚC khi code
Đây là ràng buộc nặng nhất của change. Hôm nay `_rank` là **hàm thuần** và RS harness chạy trong `pytest`
mặc định, 0 đồng, tất định, với `_NoModel` nổ khi bị chạm. Đẩy lọc thô xuống SQL phá điều đó.

Ba phương án, phải chốt một trong `design.md` trước khi implement:

| | cách làm | được | mất |
|---|---|---|---|
| **A** | fixture mang luôn `chunk_embeddings.jsonl`; `_rank` vẫn thuần, nhận sẵn `chunk_ranks` do caller tính | RS giữ nguyên tính chất | production và harness đi hai đường tính `chunk_ranks` khác nhau — đúng loại lệch im lặng |
| **B** | tách `retrieve_candidates()` (chạm DB) khỏi `rank()` (thuần); RS đo `rank()`, thêm harness nhỏ đo `retrieve_candidates` cần DB | ranh giới rõ, RS vẫn miễn phí | thêm một bộ đo, và phần chạm DB không có lưới trong `pytest` mặc định |
| **C** | fixture đông lạnh **kết quả truy vấn** `ORDER BY <=>` cho từng câu hỏi kịch bản | tất định, miễn phí, đo đúng đường production | fixture phải sinh lại mỗi lần đổi chunk/model; thêm file thứ sáu |

**Khuyến nghị: B + C** — B cho ranh giới, C cho fixture của phần chạm DB. A bị loại vì nó tái tạo đúng
chế độ hỏng "hai đường tính khác nhau, không có gì báo lỗi".

### D5 — Ngưỡng: vẫn KHÔNG có
Chunk chỉ thêm một số hạng RRF. `LIMIT n` trong SQL là **cắt để lấy ứng viên**, không phải ngưỡng
similarity — tập ứng viên cuối vẫn không bao giờ rỗng vì "không chunk nào đủ giống". Ngưỡng 0,65 của báo
cáo To‑Be vẫn bị loại, cùng lý do như `chat-hybrid-retrieval`.

### D6 — Vòng đời và purge
- Sinh khi `AnalyzerService` publish insight (cùng chỗ với `_attach_embedding`); lỗi → không có chunk +
  WARNING, **không** chặn tạo insight.
- `python -m app.scripts.chunk_documents` (idempotent, chỉ đụng bài chưa có chunk) + `--redo`.
- `purge_expired` xoá chunk cùng lúc xoá `normalized_content` — nếu không, corpus vector giữ nội dung mà
  chính sách lưu trữ đã yêu cầu xoá.
- Lượt embed chunk **không** tính vào `MAX_DAILY_CHAT_CALLS` / `MAX_DAILY_ANALYSIS` (cùng lý do với embed
  insight: khác đơn vị budget).

## API

**Không đổi.** Không endpoint mới, không field mới. Change này hoàn toàn nằm trong tầng xếp hạng.

## DB

Migration mới (sau 013):

```sql
CREATE TABLE document_chunks (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_document_id  UUID NOT NULL REFERENCES raw_documents(id) ON DELETE CASCADE,
  insight_id       UUID     NULL REFERENCES insights(id)      ON DELETE CASCADE,
  ordinal          INT  NOT NULL,
  content          TEXT NOT NULL,
  embedding        vector(768),
  created_at       TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (raw_document_id, ordinal)
);
CREATE INDEX ix_document_chunks_embedding ON document_chunks
  USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ix_document_chunks_insight ON document_chunks (insight_id);
```

`insight_id` nullable: chunk sinh lúc ingest có thể có trước khi insight tồn tại; nối lại khi publish.

## Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Mất bộ đo xếp hạng miễn phí | D4 — chốt phương án **trước** khi code; đây là điều kiện chặn |
| Chunk lạc đề đẩy bài rác lên | RRF chỉ đọc thứ hạng; `score_for_role` vẫn là khoá phụ; D1 dùng chunk tốt nhất |
| Trộn hai họ vector | cùng model/chiều với `insights.embedding`; đổi hằng số chunk ⇒ backfill toàn bộ |
| Dung lượng + thời gian ingest | chunk tối đa ~6/bài do trần 8.000 ký tự; ingest là tác vụ nền |
| Làm xong mà không ai được lợi | **Task 0 gate** — đo chế độ hỏng trước, đóng change nếu dưới ngưỡng |
