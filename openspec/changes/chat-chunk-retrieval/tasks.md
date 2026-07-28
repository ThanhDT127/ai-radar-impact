# Tasks: chat-chunk-retrieval

Phase: **P2**, **sau** `chat-context-depth`. Task 0 là **cổng chặn** — không qua thì đóng change.

## 0. Gate — đo trước, quyết sau

- [x] **0.1 (P2)** Soạn ~15 kịch bản **"khám phá bằng chi tiết"**: câu hỏi mà định danh chỉ tồn tại trong
      `normalized_content`, không có trong `title/signal/so_what/summary_short/topics`. Rút định danh ứng
      viên bằng script kiểu `eval/` của `chat-context-depth` (từ xuất hiện ≥2 lần trong thân bài, vắng
      trong biểu diễn truy hồi).
      *DoD:* file kịch bản + `label_reason` cho từng ca; mỗi ca chỉ đúng một insight `must_have`.
- [x] **0.2 (P2)** Đo `_rank` hiện tại trên bộ đó (miễn phí, tất định).
      *DoD:* bảng recall@5 / recall@60 / hạng xấu nhất per‑ca, lưu vào `measurement.md`.
      *Dep:* 0.1
- [x] **0.3 (P2)** **Quyết định ghi thành văn**: ≥ 30% ca có bài đúng ngoài top‑5 ⇒ tiếp tục. Dưới ngưỡng
      ⇒ **đóng change**, ghi lý do vào `proposal.md`, giữ bộ kịch bản lại làm mốc.
      *DoD:* một đoạn kết luận có số, không phải cảm nhận.
      *Dep:* 0.2
- [x] **0.4 (P2)** Chốt phương án giữ `chat_rank_harness` miễn phí (design D4: A / B / C). **Chặn mọi task
      còn lại.**
      *DoD:* `design.md` mục D4 ghi rõ phương án đã chọn + lý do loại hai phương án kia.
      *Dep:* 0.3

## DB migration

- [x] **1.1 (P2)** Migration bảng `document_chunks` + index HNSW cosine + index `insight_id`.
      *DoD:* `alembic upgrade head` / `downgrade -1` sạch trên DB rỗng và DB có dữ liệu.
      *Dep:* 0.4
- [x] **1.2 (P2)** Model SQLAlchemy `DocumentChunk` + quan hệ tới `RawDocument`/`Insight`.
      *DoD:* quan hệ nạp được bằng `selectinload`, không N+1.
      *Dep:* 1.1

## AI / Pipeline

- [x] **2.1 (P2)** `app/ai/chunking.py::split_content()` — cửa sổ 400–600 token, overlap ~15%, cắt ưu tiên
      `\n\n` rồi `.`, **không** cắt giữa câu. Hằng số là hợp đồng embedding (design D3).
      *DoD:* test: bài 8.000 ký tự → ≤6 chunk, không chunk nào cắt giữa từ; hàm tất định.
- [x] **2.2 (P2)** Sinh chunk + embedding trong `AnalyzerService` khi publish (cạnh `_attach_embedding`);
      lỗi → WARNING, **không** chặn tạo insight.
      *DoD:* test: embed lỗi → insight vẫn tạo, `document_chunks` rỗng cho bài đó.
      *Dep:* 1.2, 2.1
- [x] **2.3 (P2)** `app/scripts/chunk_documents.py` — backfill idempotent (chỉ đụng bài chưa có chunk) +
      `--redo`. Ghi vào CLAUDE.md phần lệnh.
      *DoD:* chạy hai lần liên tiếp → lần hai không đổi gì.
      *Dep:* 2.2
- [x] **2.4 (P2)** `purge_expired` xoá chunk cùng lúc xoá `normalized_content`.
      *DoD:* test: purge một bài → chunk của bài đó biến mất.
      *Dep:* 1.2

## Backend — retrieval

- [x] **3.1 (P2)** `retrieve_chunk_ranks(question_vector, limit)` trong repository: `ORDER BY embedding <=>`
      trên `document_chunks`, gộp về `insight_id` lấy **thứ hạng tốt nhất** (design D1).
      *DoD:* trả `dict[insight_id, rank]`; test trên DB seed nhỏ.
      *Dep:* 1.2, 0.4
- [x] **3.2 (P2)** `_rank` nhận `chunk_ranks` và thêm số hạng RRF thứ ba; insight thiếu chunk **mượn**
      `r_vec` của chính nó (design D2).
      *DoD:* test `test_insight_without_chunks_is_not_penalized` — tin khớp chính xác nhưng chưa chunk
      không thua tin lạc đề đã chunk.
      *Dep:* 3.1
- [x] **3.3 (P2)** Nối vào `_answer_global`: chạy song song với `list_for_chat` và `_embed_question`
      (`asyncio.gather`), suy giảm êm khi truy vấn chunk lỗi → bỏ số hạng thứ ba.
      *DoD:* test: chunk query ném lỗi → thứ tự **trùng khít** bản hai tín hiệu.
      *Dep:* 3.2

## Test / Eval

- [x] **4.1 (P2)** Thực thi phương án D4 đã chốt ở 0.4 (tách `retrieve_candidates` / fixture đông lạnh /
      cả hai) để `chat_rank_harness` vẫn chạy trong `pytest` mặc định, 0 đồng, `_NoModel` vẫn nổ.
      *DoD:* `docker compose exec backend python -m pytest tests/eval/ -q` xanh khi **tắt DB**.
      *Dep:* 3.2
- [x] **4.2 (P2)** Land bộ kịch bản 0.1 vào `chat_scenarios.jsonl` (group `detail_discovery`) + sinh query
      vector; chốt lại baseline RS kèm lý do.
      *DoD:* recall@5 nhóm `detail_discovery` tăng rõ so với số đo 0.2; không nhóm nào tụt.
      *Dep:* 4.1
- [x] **4.3 (P2)** `chat_answer_harness --live` — context đổi ⇒ câu trả lời đổi; chốt lại baseline.
      *DoD:* Faithfulness ≥ 0,95 **và** Citation Precision = 1,00.
      *Dep:* 3.3
- [x] **4.4 (P2)** Test bất biến "chunk không phải đích citation": mọi mapping `n → nguồn` chỉ chứa insight.
      *DoD:* `tests/test_chunk_not_citable.py`.
      *Dep:* 3.3

## DevOps

- [x] **5.1 (P2)** Đo dung lượng + thời gian: số chunk thật, MB vector, thời gian backfill toàn corpus,
      độ trễ thêm vào mỗi câu hỏi.
      *DoD:* số ghi vào `measurement.md`; nếu độ trễ thêm > 0,5s thì mở lại thiết kế `limit` của 3.1.
      *Dep:* 2.3, 3.3
