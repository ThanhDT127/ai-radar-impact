## Context

Báo cáo To‑Be mục 3.2 #2 giải Nguy hiểm #2 (SQL keyword thất bại trước câu ngữ nghĩa) bằng **Hybrid Search
(pgvector) + RRF**. Hiện `_rank` (`chat_service.py:260`) xếp hạng bằng keyword thuần → mù đồng nghĩa
(sa thải ↔ *layoff*). `config.yaml` đã dự trù pgvector cho Phase 2. Đây là change cuối, đóng trọn khung 7 phần.

Fork đã chốt (23/07/2026): **A** = embedding Google qua Vertex (`text-multilingual-embedding-002`, 768);
**B** = mỗi insight một vector, không chunk; **C** = RRF + top‑K, **không** ngưỡng.

**Module ảnh hưởng:** M8 (Chatbot/Search) + chạm M4 (analysis embed khi publish).
**API endpoints:** không thêm/sửa/xoá; `_rank` đổi bên trong, request/response giữ nguyên.
**Bảng DB:** **migration 012** — `CREATE EXTENSION vector`; `insights.embedding vector(768)` + index cosine.
Cần image Postgres có pgvector.
**AI/LLM:** embedding Vertex `text-multilingual-embedding-002` (768) qua `google-genai` + key GCP SA hiện có
(cùng đường Gemini). Embedding **không** phải generation → tách quota. `CHAT_SYSTEM_PROMPT`/grounding/citation
giữ nguyên.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Bắt được câu ngữ nghĩa lệch từ khoá; nâng recall (đo bằng RS harness, phải tăng không giảm).
- Không tái sinh "rỗng → báo nhầm không có tin"; không thêm vendor; chat không gãy khi embedding lỗi.

**Non-Goals:**
- Không chunk raw_documents; không ngưỡng cứng; không rerank cross‑encoder; không đổi mode B/grounding/streaming.

## Decisions

### D1 — Embedding Vertex `text-multilingual-embedding-002`, 768 chiều

Dùng lại đúng auth GCP SA + SDK `google-genai` đang chạy Gemini → **0 vendor mới, 0 key mới**. Model
multilingual (không phải `text-embedding-004` thiên Anh) vì corpus trộn Việt–Anh kỹ thuật. **768** chốt cứng
vào cột `vector(768)` của migration — đổi chiều sau là đổi schema, nên cố định từ đầu. Nếu `google-genai==0.8.0`
chưa expose embedding thì task đầu **xác minh + chốt cách gọi** trước khi migration.

### D2 — Mỗi insight một vector, text cô đọng; không chunk

Đơn vị retrieval toàn cục là **insight** (ngắn), không phải đoạn bài. Embed từ chuỗi cô đọng:
`title + signal + so_what + summary_short + topics`. Không chunk `raw_documents`: mode B đã nhồi cả bài nên
không cần truy hồi đoạn; chunk chỉ đáng khi bài dài cần định vị đoạn — để dành. Định nghĩa hàm dựng
"embedding text" một chỗ, dùng chung lúc ingest và (nếu cần) lúc so khớp.

### D3 — Xếp hạng lai: RRF(vector, lexical) → độ‑quan‑trọng → top‑K, KHÔNG ngưỡng

Giữ kiến trúc hai tầng, chỉ **nâng tầng độ‑liên‑quan** từ keyword thuần thành **trộn**:
```
rrf(d) = 1/(60 + rank_vector(d)) + 1/(60 + rank_lexical(d))
key xếp hạng = ( rrf(d), score_for_role(d) )   → sort giảm dần → cắt chat_index_top_k
```
`rank_lexical` từ `_relevance` biên‑từ (sau CI); `rank_vector` từ cosine giữa embedding câu hỏi và insight.
**Không ngưỡng similarity**: chỉ dùng vector để **xếp hạng tốt hơn**, vẫn cắt top‑K nên **không bao giờ rỗng** —
giữ đúng bài học đã ghi ("xếp hạng, không lọc ngưỡng"). Ngưỡng 0,65 của báo cáo bị loại vì tái sinh Nguy hiểm #2.

*Đã cân nhắc:* thay hẳn lexical bằng vector. Bỏ — vector kém ở khớp **chính xác** (tên model, mã CVE, số
phiên bản); RRF giữ cả hai điểm mạnh, đúng lý do dùng *hybrid* chứ không *vector‑only*.

### D4 — Migration = schema; backfill = script (migration không gọi Vertex)

Migration 012 chỉ đụng schema (extension + cột + index) — **không** gọi API embedding (migration phải tất
định, offline). Backfill 179 tin cũ bằng script chạy tay một lần (`embed_insights.py`), giữ lại làm công cụ.
Insight mới: `AnalyzerService` embed **khi publish** (thêm 1 lượt embed, rẻ). Tin chưa có embedding (đang
backfill dở) → D6 lo (vẫn tham gia qua lexical).

### D5 — pgvector phải có trong image Postgres (infra)

`CREATE EXTENSION vector` cần extension cài sẵn. `postgres:16` trần **không** có → đổi image sang
`pgvector/pgvector:pg16` (hoặc cài thêm) trong `docker-compose`. Đây là thay đổi hạ tầng thật, task riêng,
kiểm trước khi chạy migration.

### D6 — Suy giảm êm: embedding lỗi/thiếu → xếp hạng lexical, chat không gãy

Embedding là **phụ trợ xếp hạng**, không phải đường sống của chat. Nếu embed câu hỏi lỗi/timeout (Vertex sự
cố) → bỏ tầng vector, xếp bằng lexical như hiện tại, log WARNING. Insight có `embedding IS NULL` → không tham
gia rank_vector nhưng **vẫn** qua rank_lexical (không bị rơi). Không bao giờ để lỗi embedding làm hỏng câu trả
lời — chỉ làm nó kém ngữ nghĩa hơn tạm thời.

### D7 — RS là cổng bắt buộc; ⑥ phải re‑baseline và chứng minh recall tăng

⑥ sửa `_rank` → RS harness là thứ **duy nhất** bắt hồi quy. Quy trình: chạy RS trước (baseline cũ) → áp
hybrid → chạy lại → recall nhóm ngữ nghĩa **phải tăng rõ**, tổng **không giảm** câu nào → **chốt lại baseline
ở mức mới** (luật baseline RS). Nếu một nhóm tụt, dừng, không land.

## Risks / Trade-offs

- **[pgvector image/infra]** → D5 task riêng + kiểm `CREATE EXTENSION` chạy được trước khi viết migration data.
- **[SDK 0.8.0 có embedding không]** → task đầu xác minh cách gọi; nếu bí, cân nhắc endpoint embedding Vertex
  trực tiếp — **trước** khi cố định 768 vào schema.
- **[Backfill tốn lượt embed × 179]** → rẻ (embedding ≪ generation); chạy một lần, có rate‑limit.
- **[Query embedding thêm độ trễ]** → ~chục–trăm ms, không đáng so với generation 5–22s; và fallback lexical
  khi lỗi (D6).
- **[Đổi `_rank` phá recall ngoài dự kiến]** → D7: RS gác, re‑baseline có chủ đích, per‑câu; không "chỉnh số
  cho xanh".
- **[Vector kém khớp chính xác]** → RRF giữ lexical nên tên model/CVE/version vẫn bắt đúng (D3).

## Migration Plan

1. Xác minh cách gọi embedding qua `google-genai`/Vertex (D2 model, 768) — **trước** khi cố định schema.
2. Infra: đổi image Postgres sang bản có pgvector; kiểm `CREATE EXTENSION vector`.
3. Migration 012: extension + `insights.embedding vector(768)` + index cosine.
4. Backend: hàm embed (client) + `AnalyzerService` embed khi publish + hàm dựng embedding‑text (D2).
5. Script backfill 179 tin cũ.
6. `_rank` → hybrid RRF + top‑K, không ngưỡng, fallback lexical (D3, D6).
7. Chạy lại **RS harness**, đối chiếu recall, **chốt lại baseline** (D7).
8. Docs.

Rollback: `_rank` revert về keyword (giữ được vì D6 vẫn có đường lexical); cột/extension để lại vô hại hoặc
drop bằng downgrade. Không mất dữ liệu insight.

## Open Questions

- **Loại index vector** (HNSW vs IVFFlat): HNSW recall tốt hơn, IVFFlat nhẹ hơn; ở 179→vài nghìn tin khác
  biệt nhỏ — chọn HNSW nếu pgvector image hỗ trợ, xác nhận ở bước infra.
- **Rerank cross‑encoder**: hoãn; cân nhắc nếu RRF vẫn để sót ca ngữ nghĩa khó sau khi đo thật.
- **Embed cả `raw_documents` (chunk)**: mở lại khi cần Q&A định vị đoạn trong bài dài (ngoài phạm vi ⑥).
