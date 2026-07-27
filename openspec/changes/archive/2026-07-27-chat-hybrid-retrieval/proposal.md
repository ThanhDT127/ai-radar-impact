# Proposal: chat-hybrid-retrieval

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — phủ phần 1 khung To‑Be: Retrieval & RAG. Đóng trọn 7 phần).

## Why

Retrieval hiện tại **mù ngữ nghĩa** (Nguy hiểm #2): `_rank` xếp hạng bằng **so khớp từ khoá** (`_relevance`
đếm từ câu hỏi xuất hiện trong tin). Người dùng hỏi "các tập đoàn cắt giảm nhân sự mảng AI" trong khi tin
lưu chữ *layoff / downsizing / headcount* → từ khoá không khớp → tin đúng xếp hạng thấp → **bị cắt khỏi
top‑K**, và model không bao giờ thấy. Đây là chế độ hỏng im lặng mà `chat-rank-stability` đo được nhưng
không **chữa** — nó chỉ canh recall của cơ chế keyword.

`config.yaml` đã dự trù pgvector cho đúng Phase 2 này. Cải thiện ở đây cũng **nâng luôn** chất lượng phần
mở rộng của `chat-scope-routing` (③) — vốn khai dependency mềm chờ ⑥.

## What Changes

- **Embedding tiếng Việt qua Vertex** (chốt 23/07): dùng model embedding của Google qua chính key GCP SA
  đang chạy Gemini — `text-multilingual-embedding-002`, **768 chiều**. Không thêm vendor mới.
- **Cột vector + pgvector**: bật extension `pgvector`, thêm `insights.embedding vector(768)` + index. Mỗi
  insight **một vector** dựng từ text cô đọng (title/signal/so_what/summary_short/topics) — **không chunk**
  (insight vốn ngắn; chunk là over‑engineering ở quy mô này).
- **Xếp hạng lai (RRF)**: trộn thứ hạng **vector** (tương đồng ngữ nghĩa) và **lexical** (từ khoá hiện có)
  bằng Reciprocal Rank Fusion `1/(60+rank)`, rồi **giữ nguyên tầng độ‑quan‑trọng** `score_for_role` làm khoá
  phụ, rồi **cắt top‑K**. **KHÔNG ngưỡng similarity** — giữ đúng bài học "xếp hạng, không lọc, không bao giờ
  rỗng"; ngưỡng cứng sẽ tái sinh Nguy hiểm #2.
- **Vòng đời embedding**: sinh khi publish insight (trong analysis), backfill 179 tin cũ bằng script, và
  embed câu hỏi mỗi request (1 lượt embedding, rẻ, tách khỏi quota generation). **Suy giảm êm**: embedding
  lỗi/thiếu → rơi về xếp hạng lexical, chat **không** gãy.

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-qa-service`: retrieval toàn cục SHALL xếp hạng bằng trộn vector + lexical (RRF) rồi tầng độ‑quan‑trọng
  và top‑K, không ngưỡng; hệ thống SHALL duy trì embedding cho mỗi insight và suy giảm êm khi embedding vắng.

## Non-goals

- **Không** chunk `raw_documents` / truy hồi đoạn — mode B đã nhồi cả bài; để dành khi corpus/bài dài cần.
- **Không** ngưỡng similarity cứng (giữ never‑empty).
- **Không** thêm vendor (OpenAI/local) — dùng Vertex.
- **Không** rerank cross‑encoder giai đoạn này — RRF đủ cho v1; rerank cân nhắc khi có tín hiệu.
- **Không** đổi mode B, grounding, citation, fail‑closed, streaming.

## Dependencies

- **`chat-rank-stability` (RS) — cứng, land trước**: ⑥ **sửa `_rank`**, nên bắt buộc chạy lại harness và
  **chốt lại baseline** (đúng "luật baseline" của RS). ⑥ phải cho recall **tăng**, đặc biệt nhóm câu ngữ nghĩa.
- **`chat-citation-integrity` (CI) — cứng, land trước**: CI sửa tầng lexical (`_relevance` biên‑từ); ⑥ trộn
  vector **lên trên** tầng lexical đã sửa đó.
- **`chat-scope-routing` (③) — bổ trợ**: phần mở rộng của ③ tự hưởng recall ngữ nghĩa tốt hơn.
- `chatbot-qa` (archive 22/07/2026); `config.yaml` (pgvector Phase 2).

## Impact

- **DB migration (012)**: `CREATE EXTENSION vector`; `insights.embedding vector(768)` + index (HNSW/cosine).
  **Cần image Postgres có pgvector** (đổi sang `pgvector/pgvector:pg16` hoặc cài extension) — infra.
- **Backend**: `ai/gemini_client.py` (hàm embed qua Vertex), `services/analyzer.py` (embed khi publish),
  `services/chat_service.py` (`_rank` → hybrid + embed câu hỏi + fallback lexical), script backfill, test.
- **AI/LLM**: embedding `text-multilingual-embedding-002` (768) qua Vertex; 1 lượt embed/insight (ingest) +
  1 lượt embed/câu hỏi (chat). Tách khỏi quota generation.
- **Docs**: `CLAUDE.md` — hybrid RRF, không ngưỡng, fallback lexical, chạy lại RS + re‑baseline.
