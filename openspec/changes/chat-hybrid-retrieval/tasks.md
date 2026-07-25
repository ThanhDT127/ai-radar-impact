# Tasks: chat-hybrid-retrieval

**Phase:** 2 (M8 Chatbot + chạm M4). Backend + DB migration + AI + Test. Không n8n, không Frontend.

> Phụ thuộc cứng: **`chat-rank-stability` (RS) và `chat-citation-integrity` (CI) land trước**. ⑥ sửa `_rank`
> nên **bắt buộc** chạy lại RS harness và chốt lại baseline (D7). Thứ tự: xác minh embedding → infra pgvector
> → migration → embed pipeline → hybrid rank → đo lại RS → docs.

## 0. Xác minh trước khi cố định schema (Backend/AI)

- [ ] 0.1 Xác minh cách gọi embedding qua `google-genai==0.8.0` + Vertex với model `text-multilingual-embedding-002`, xác nhận **768 chiều** (design D1, D2). Nếu SDK chưa expose, chốt đường gọi thay thế **trước** khi viết migration. **DoD:** một đoạn thử trả về vector 768 chiều từ một chuỗi tiếng Việt.

## 1. Hạ tầng pgvector (DevOps)

- [ ] 1.1 Đổi image Postgres sang bản có pgvector (`pgvector/pgvector:pg16` hoặc cài extension) trong `docker-compose` (design D5). **DoD:** `CREATE EXTENSION IF NOT EXISTS vector;` chạy được trong container DB.

## 2. Migration 012 (DB)

- [ ] 2.1 Migration: `CREATE EXTENSION vector`; thêm `insights.embedding vector(768)` (nullable); index cosine (HNSW nếu image hỗ trợ, else IVFFlat — Open Question). **KHÔNG** gọi API embedding trong migration (design D4). **DoD:** `alembic upgrade head` và `downgrade -1` chạy sạch; cột + index tồn tại.

## 3. Vòng đời embedding (Backend/AI)

- [ ] 3.1 Hàm embed trong `gemini_client` (Vertex, 768), tách khỏi generation; trả vector + đếm lượt riêng. **DoD:** gọi được, không đụng quota generation.
- [ ] 3.2 Hàm dựng "embedding text" của insight một chỗ: `title + signal + so_what + summary_short + topics` (design D2). **DoD:** dùng chung ingest + backfill, không lặp định nghĩa.
- [ ] 3.3 `AnalyzerService`: embed và lưu khi publish insight (thêm 1 lượt embed). Lỗi embed **không** chặn việc tạo insight — để `embedding NULL`, log WARNING (design D6). **DoD:** insight mới có embedding; embed lỗi vẫn tạo được insight.
- [ ] 3.4 Script `embed_insights.py` backfill mọi insight `published`+`is_primary` đang `embedding IS NULL`, có rate‑limit, chạy lại được (idempotent). Giữ lại làm công cụ. **DoD:** chạy xong 179 tin có embedding; chạy lại không trùng lặp.

## 4. Xếp hạng lai (Backend)

- [ ] 4.1 Embed câu hỏi mỗi request chat (1 lượt embed); lỗi/timeout → bỏ tầng vector, xếp bằng lexical, log WARNING (design D6). **DoD:** tắt mạng Vertek embed → chat vẫn trả lời (kém ngữ nghĩa), không 500.
- [ ] 4.2 `_rank` → **RRF**: trộn `rank_vector` (cosine embedding) và `rank_lexical` (`_relevance` biên‑từ sau CI) bằng `1/(60+rank)`, rồi khoá phụ `score_for_role`, rồi cắt `chat_index_top_k`. **KHÔNG ngưỡng** (design D3). **DoD:** tin lệch từ khoá nhưng gần ngữ nghĩa (sa thải↔layoff) lọt top‑K; không có ca trả về rỗng vì ngưỡng.
- [ ] 4.3 Insight `embedding IS NULL` vẫn tham gia qua lexical, không bị rơi (design D6). **DoD:** test: một tin chưa embed vẫn xuất hiện được trong index qua đường lexical.
- [ ] 4.4 Phần mở rộng của `chat-scope-routing` (③) tự dùng đường hybrid này (không code riêng). **DoD:** câu out‑of‑scope của ③ hưởng recall ngữ nghĩa.

## 5. Đo lại RS + baseline (Test) — CỔNG BẮT BUỘC

- [ ] 5.1 Chạy RS harness **trước** khi áp hybrid (baseline cũ) rồi **sau**, ghi số per‑câu. Recall nhóm ngữ nghĩa **phải tăng rõ**; tổng **không câu nào tụt**. **DoD:** bảng recall trước/sau; nếu một câu tụt thì dừng, không land (design D7).
- [ ] 5.2 **Chốt lại baseline RS ở mức mới** kèm lý do (luật baseline RS). **DoD:** hằng số baseline RS khớp số "sau", có ngày + ghi "do chat-hybrid-retrieval nâng recall".
- [ ] 5.3 Thêm ca truy vấn ngữ nghĩa lệch‑từ‑khoá vào bộ câu RS (vd "cắt giảm nhân sự" khi tin ghi *layoff*) nếu chưa có, để chính bộ đo phủ được chế độ hỏng ⑥ chữa. **DoD:** bộ RS có ≥1 ca ngữ nghĩa; ca đó recall thấp trước, cao sau.

## 6. Tài liệu (làm sau khi code đã chạy)

- [ ] 6.1 `CLAUDE.md` mục chat: retrieval **lai** (RRF vector+lexical), **không ngưỡng** (giữ never‑empty), embedding Vertex 768, **fallback lexical** khi embed lỗi, và **phải chạy lại RS + re‑baseline** khi đụng `_rank`/embedding. **DoD:** người đọc hiểu vì sao không đặt ngưỡng similarity.
- [ ] 6.2 Ghi migration 012 + yêu cầu image pgvector vào tài liệu vận hành. **DoD:** ai dựng lại môi trường biết phải dùng image có pgvector.
