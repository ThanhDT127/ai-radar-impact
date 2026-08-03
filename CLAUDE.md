# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Radar Impact** is a full-stack web application that ingests RSS feeds, analyzes them with Google Vertex AI (Gemini 2.5 Flash), and surfaces AI-impact insights in Vietnamese. Backend: FastAPI + PostgreSQL (async). Frontend: React 19 + Vite + TanStack Query.

## Development Commands

All services run via Docker Compose. The frontend dev server proxies `/api` to the backend.

```bash
# Start all services (PostgreSQL, FastAPI, Vite dev server)
docker-compose up

# Run database migrations
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic downgrade -1

# Frontend standalone (outside Docker)
cd frontend && npm install && npm run dev    # port 5173
cd frontend && npm run build                # tsc + vite build
```

### Data Pipeline Scripts

```bash
# Seed initial RSS sources
docker-compose exec backend python -m app.scripts.seed_sources

# Ingest all active sources (or single source by UUID)
docker-compose exec backend python -m app.scripts.run_ingestion
docker-compose exec backend python -m app.scripts.run_ingestion --source-id <UUID>

# Analyze pending raw documents via Gemini
docker-compose exec backend python -m app.scripts.run_analysis

# Backfill embedding cho chat hybrid retrieval (idempotent — chỉ đụng hàng embedding NULL)
docker-compose exec backend python -m app.scripts.embed_insights
docker-compose exec backend python -m app.scripts.embed_insights --redo   # đổi model/embedding text

# Backfill ĐOẠN thân bài + embedding cho tín hiệu xếp hạng thứ ba (idempotent — chỉ bài chưa có đoạn)
docker-compose exec backend python -m app.scripts.chunk_documents
docker-compose exec backend python -m app.scripts.chunk_documents --dry-run   # chỉ đếm, 0 đồng
docker-compose exec backend python -m app.scripts.chunk_documents --redo      # đổi hằng số chunk/model

# Maintenance
docker-compose exec backend python -m app.scripts.reset_failed       # re-queue failed docs
docker-compose exec backend python -m app.scripts.cleanup_en_insights # remove English insights

# Delivery: chạy tay một kỳ bản tin (dry-run in nội dung, không gửi, không ghi log)
docker-compose exec backend python -m app.scripts.run_delivery --dry-run
docker-compose exec backend python -m app.scripts.run_delivery --send
```

## Architecture

### Data Flow

```
RSS Sources → IngestionService → RawDocument (pending)
                                      ↓
                              AnalyzerService → GeminiClient (Vertex AI)
                                      ↓
                              Insight (published) → FastAPI Routes → React UI
```

### Backend (`backend/app/`)

Layered architecture with strict separation:

- **`connectors/`** — RSS (`RSSConnector` via feedparser), HackerNews, Reddit, WebArticle (utility), **`GitHubTrendingConnector`** (scrape `github.com/trending` HTML), **`HuggingFaceConnector`** (HF public API for org models — no auth), **`WebIndexConnector`** (scrape index page + extract article URLs + fetch each via trafilatura). Tất cả auto-register vào `ConnectorRegistry`. `source_type` values: `rss`, `hackernews`, `reddit`, `github_trending`, `huggingface`, `web_index`.
- **`services/`** — Business logic: `IngestionService` (fetch → normalize → dedup → store), `AnalyzerService` (pending docs → Gemini → Insight)
- **`ai/`** — `GeminiClient` wraps google-genai SDK; prompt templates define allowed topics/event_types/roles in Vietnamese
- **`repositories/`** — Data access layer (InsightRepository, RawDocumentRepository, SourceRepository)
- **`models/`** — SQLAlchemy async ORM (UUIDs, PostgreSQL arrays)
- **`schemas/`** — Pydantic v2 request/response validation
- **`routes/`** — FastAPI endpoints under `/api/v1/`
- **`channels/`** — `ChannelAdapter` interface + `DeliveryMessage` (channel-neutral) + Registry pattern như connectors. **`EmailAdapter`** (`channels/email.py`, `channel_type="email"`) gửi qua SMTP bằng `aiosmtplib`, một email/một địa chỉ `To:` (không BCC), `multipart/alternative` + header `List-Unsubscribe`. Adapter có hook `open()`/`close()` (mặc định no-op) để mở 1 kết nối SMTP cho cả lượt gửi. `channels/email_templates.py` render `(subject, text, html)` bằng f-string thuần — không có template engine.
- **`services/delivery_engine.py`** — M7 Delivery: bản tin định kỳ **Thứ Hai + Thứ Năm** (giờ VN, lookback 108h), nhóm theo vai trò, **chọn tin bằng xếp hạng rồi lấy top-N cứng** (2 tin/vai trò, trần 3 tin/email) chứ không lọc theo ngưỡng; chống trùng qua `delivery_log` unique (insight_id, subscriber_id, kind); thuần template, KHÔNG gọi Gemini. **Channel-neutral** (nhận `ChannelAdapter`).
- **`config.py`** — `BaseSettings` reads from `.env`; `database.py` creates async engine

Key rules in `AnalyzerService`:
- Insights with `confidence < 0.3` are discarded
- `trust_tier` → `trust_score` is rule-based (not AI-generated)
- `event_type` → `impact_label` mapping is hardcoded in Vietnamese

### Frontend (`frontend/src/`)

- **`api/`** — Axios client with `baseURL=/api/v1`; functions map to backend endpoints
- **`pages/`** — `InsightList.tsx` (paginated dashboard with filters/stats), `InsightDetail.tsx`
- **`components/`** — Presentational components; CSS Modules for styling
- **`App.tsx`** — React Router setup

State: TanStack Query for all server state. Local React state for UI (page, filters, sort).

### Database

PostgreSQL 16 **có pgvector** — image phải là `pgvector/pgvector:pg16`, KHÔNG phải `postgres:16` trần (đổi 27/07/2026, migration 012 `CREATE EXTENSION vector` + `insights.embedding vector(768)` + index HNSW cosine). Dựng lại môi trường bằng image không có extension thì `alembic upgrade head` đỏ ngay ở 012. All PKs are UUIDs. Deduplication uses SHA256 fingerprints computed from **`source_url` + `title`** (see `normalizer.make_fingerprint`), not from content body. Migrations are in `backend/alembic/`.

> ⚠️ **Đổi image từ `postgres:16-alpine` trên volume `pgdata` CŨ**: alpine dùng musl, image pgvector dùng glibc, mà hai libc sắp xếp `en_US.utf8` khác nhau ⇒ chạy `REINDEX DATABASE ai_radar` ngay sau khi đổi (dữ liệu và layout PG16 thì tương thích, không phải dump/restore). Dựng mới hoàn toàn thì không cần.
>
> Sau migration 012, cột `embedding` **rỗng** — nó là schema, không phải dữ liệu (migration cố ý không gọi Vertex). Backfill bằng `docker compose exec backend python -m app.scripts.embed_insights`.
>
> Migration **014** thêm bảng `document_chunks` (đoạn thân bài + `vector(768)` + HNSW cosine) — cũng **rỗng sau migration**, backfill bằng `python -m app.scripts.chunk_documents`. Đo 28/07: 179 bài → **535 đoạn**, bảng 5,4MB kể cả index, backfill 1 phút 55.

Key models: `Source` (RSS feeds with trust_tier, **`region`** ∈ `global`/`china`/`vietnam`, **`target_roles`** VARCHAR[]) → `RawDocument` (fetched content, processing_status) → `Insight` (analyzed output). Delivery: `Subscriber` (id UUID PK, `email` unique, roles[] từ `ALLOWED_ROLES`, active, `unsubscribe_token`) + `DeliveryLog` (unique insight_id+subscriber_id+kind — idempotent).

`Source.region` tagging (added 2026-05-09): `global` (default for Western sources), `china` (China AI orgs + analyst newsletters like Interconnects/ChinaTalk/ChinAI), `vietnam` (Vietnamese news/community). `target_roles` is hint metadata for ingestion strategy.

## Environment Setup

Copy `.env.example` to `.env` and fill in:

```env
DATABASE_URL=postgresql+asyncpg://radar:radar_dev@db:5432/ai_radar
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1   # must be a specific region, not "global"
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa-key.json
```

Place the GCP Service Account JSON key at `secrets/sa-key.json` (mounted read-only into the backend container). This file is gitignored.

## Key Constraints

- All user-facing text, AI prompts, topics, roles, and event_type labels are in **Vietnamese**.
- The Gemini prompt enforces a closed set of allowed values for `topics`, `event_types`, and `affected_roles` — new values must be added to the prompt template in `app/ai/`.
- `GOOGLE_CLOUD_LOCATION` must be a specific region (`us-central1`), not `"global"`.
- The backend uses fully async SQLAlchemy — never use sync ORM calls.

## Insight Schema v2 (Actionable Fields)

The `insights` table has 7 actionable fields (added 2026-05-09). 4 are AI-generated, 3 are rule-based.

**AI-generated (Gemini, may be NULL on parse failure):**
- `signal` (TEXT) — 1 câu cô đọng implication, KHÁC title
- `why_it_matters` (TEXT) — 1-2 câu vì sao quan trọng với team VN
- `recommendations` (JSONB) — `{ role: { action_type, note, urgency } }`, keys ⊆ `affected_roles`
- `risks` (TEXT[]) — danh sách rủi ro nếu adopt; có thể `[]`

**Rule-based (computed in `AnalyzerService` / `DeduplicationEngine`):**
- `momentum` (`new` | `rising` | `mature`) — derive từ cluster size + age (`compute_momentum` in dedup_engine)
- `urgency` (`critical` | `high` | `medium` | `low`) — `_compute_urgency(impact_label, published_at)`
- `vietnam_relevance` (`high` | `medium` | `low`) — `_compute_vietnam_relevance(source, topics)`

**Closed set `ALLOWED_ACTION_TYPES`** (in `app/ai/prompts.py`): `watch`, `read`, `test`, `PoC`, `roadmap`.

### ⚠️ Hai khái niệm `urgency` khác nhau — đừng nhầm

| | `insights.urgency` (cột) | `recommendations[role].urgency` (khoá JSONB) |
|---|---|---|
| Nghĩa | Mức ảnh hưởng của tin **nói chung** | Mức ảnh hưởng tới **riêng một vai trò** |
| Tập giá trị | `critical`/`high`/`medium`/`low` | `high`/`medium`/`low` (`ALLOWED_ROLE_URGENCY`, **không có** `critical`) |
| Nguồn | Rule-based, suy tất định từ `impact_label` | Gemini chấm cho từng vai trò |
| Dùng để | Dashboard, sort, emoji trong digest | **Quyết định gửi alert** (ngưỡng `high`) |

Cột `insights.urgency` **không còn** quyết định alert/digest (đổi 2026-07-20, change `role-aware-alert`).
Thiếu khoá `urgency` hoặc giá trị ngoài tập đóng → coi như `medium` → không alert; nhờ vậy insight cũ
không bắn alert hồi tố.

Backwards compatible: insights cũ chưa có 7 fields trả `null`; UI hide gracefully (không render placeholder).

Regenerate insights cũ với prompt v2: `docker-compose exec backend python -m app.scripts.regenerate_insights --limit 50`.

> ⚠️ `regenerate_insights` ghi đè `signal`/`summary_short`/`topics` — đúng bộ field `build_embedding_text` dùng — nên nó **phải embed lại** (sửa 28/07/2026; trước đó vector vẫn mô tả bản phân tích CŨ và tầng vector của chat xếp hạng theo một nội dung không còn tồn tại, **không có gì báo lỗi**). Embed lỗi thì **giữ vector cũ** chứ không set NULL. `document_chunks` KHÔNG cần sinh lại — chúng cắt từ `normalized_content`, mà regenerate không đụng thân bài.

## Vietnamese Taxonomy (Closed Sets)

Defined in `backend/app/ai/prompts.py`. Adding or renaming values here requires updating the Gemini prompt **and** any frontend labels that map to them.

**Topics (`ALLOWED_TOPICS`) — 12 giá trị (v3, sửa 22/07/2026):**
AI/ML Ứng dụng, AI/ML Nghiên cứu, DevTools & Frameworks, Cloud & Infrastructure, Data Engineering, Security & Compliance, Software Architecture, Developer Experience, Platform & API, Market & Competition, Legal & Regulation, Team & Process

> ⚠️ File này từng ghi 10 topic tiếng Việt cũ (*Trí tuệ nhân tạo, Công nghệ, Dữ liệu…*) — **sai hoàn
> toàn**, không giá trị nào trùng danh sách thật. Nợ sót lại từ `taxonomy-overhaul`. Nguồn sự thật là
> `backend/app/ai/prompts.py`, không phải file này.
>
> Tập đóng này **không được thực thi** trong `analyzer.py` (vì `analyze()` cố ý không bật
> `response_schema`), nên DB đã có giá trị ngoài tập: `IoT & thiết bị` (×6) và
> `Agent / AI / Data Science` (×1) — model mượn chữ từ phần bối cảnh 4 trụ cột của `GATE_PROMPT`
> (sửa 21/07) sang phần phân loại. Vì vậy **đừng dùng topic làm filter cứng**.

**Event Types (`ALLOWED_EVENT_TYPES`):**
Phát hành mới, Thay đổi chính sách, Cập nhật quy định, Cảnh báo bảo mật, Ngừng hỗ trợ, Tín hiệu xu hướng, Thảo luận cộng đồng, Cập nhật nghiên cứu, Sự cố vận hành

**Nature (`ALLOWED_NATURES`):**
Rủi ro, Cơ hội, Tuân thủ, Thông tin chung, Theo dõi

**Affected Roles (`ALLOWED_ROLES`) — 9 vai trò:**
Data Analyst, Data Scientist, AI Engineer, Data Engineer, Security, Dev, Tech Lead, Người dùng phổ thông, Toàn công ty

Đây là bộ **chức danh** dùng cho `insights.affected_roles`, keys của `insights.recommendations`, và `Subscriber.roles` (delivery). Frontend map nhãn hiển thị trong `RoleBadge.tsx` (`ROLE_DISPLAY_LABEL`) và `TooltipContent.ts` — sửa `ALLOWED_ROLES` phải sửa kèm cả hai.

> ⚠️ **KHÔNG nhầm với `Source.target_roles`** — một taxonomy **khác**, 13 giá trị theo *chức năng phòng ban* (Executive, Engineering, Data/AI, Product, Content/Marketing, Legal/Compliance, HR/L&D, DevOps, Infrastructure, Security, BA/QA, Designer/UX, Toàn công ty). Nó là metadata chiến lược nguồn (đo độ phủ), không bao giờ xuất hiện trên insight. Định nghĩa tại `app/scripts/audit_target_roles.py::TARGET_ROLE_TAXONOMY`. Hai bộ chỉ trùng nhau ở `Security` và `Toàn công ty`.

### Rule-Based Mappings (in `AnalyzerService`)

`trust_tier` → `trust_score`:
| Tier | Score |
|------|-------|
| very_high | 0.95 |
| high | 0.80 |
| medium | 0.60 |
| low | 0.40 |
| unverified | 0.20 |

`event_type` → `impact_label`:
| Event Type | Impact Label |
|---|---|
| Cảnh báo bảo mật | Nghiêm trọng |
| Cập nhật quy định | Cao |
| Thay đổi chính sách | Cao |
| Ngừng hỗ trợ | Cao |
| Phát hành mới | Trung bình |
| Sự cố vận hành | Trung bình |
| Cập nhật nghiên cứu | Thấp |
| Tín hiệu xu hướng | Thấp |
| Thảo luận cộng đồng | Theo dõi |

Minimum confidence to publish: **0.3** (below this → `failed`, no insight created).

## Known Gotchas

- **Author field length**: `author` column has a max length constraint. Truncate to 500 chars before insert — long author strings from some RSS feeds (e.g. arXiv) cause transaction failures. Fix is in `IngestionService`.
- **Router ordering**: `/api/v1/insights/stats` must be declared **before** `/{id}` in the FastAPI router, or it gets matched as a UUID path parameter and returns 422.
- **Counting insights**: any user-facing insight count MUST filter `is_primary == True`, matching `list_paginated`. Counting raw `published` rows includes semantic-dedup duplicates that the list hides, so the number won't match what users see when they click through. In `source_repo.list_with_insight_counts` the condition belongs in the **outer join's `ON` clause, not `WHERE`** — putting it in `WHERE` drops every source with no primary insight from the response and breaks the "chưa có insight" group in the UI. Guarded by `tests/test_insight_count_queries.py`.
- **AWS What's New source name**: The source name contains a Unicode right single quotation mark (`'`, U+2019) instead of a regular apostrophe. Exact-match DB lookups against this source name must use the correct character.
- **Content limit in prompt**: Gemini prompt truncates content to 6000 chars (`prompts.py:87`). Longer articles are silently cut — this affects arXiv and long blog posts.
- **Confidence threshold mismatch**: `openspec/specs/ai-analysis/spec.md` says confidence < 0.5 → `needs_review`, but actual code uses 0.3 as the discard threshold with no `needs_review` state. The spec is aspirational; code is authoritative.
- **Tính tỉ lệ qua gate phải lọc `gate_skipped = false`**: khi gate lỗi parse, code fail-open cho doc đi thẳng vào deep analysis. Doc đó kết thúc ở `analyzed` y hệt doc qua gate thật, nên nếu đếm cả nó thì tỉ lệ qua gate bị thổi lên (đo 20/07/2026: thô 18/24/26/36% so với thật 13/17/20/22%, lệch gần gấp rưỡi). Cột `raw_documents.gate_skipped` (migration 009) đánh dấu nhóm này. **Số liệu trước 20/07/2026 có nhiễu** vì chưa có cột — doc cũ mặc định `false` và không backfill được, đừng so trực tiếp với số sau ngày đó.
- **Gate phán theo 4 TRỤ CỘT công ty (không phải IoT-only)**: `GATE_PROMPT` đánh giá impact-vs-thông-báo theo phạm vi Rạng Đông gồm **① IoT/R&D · ② Agent/AI/Data Science (phòng AI/DS) · ③ Smart Home · ④ Bảo mật hệ thống/dữ liệu (duyệt mạnh)** — sửa 21/07/2026 (change `w4-gate-accuracy`, T10). Bài chạm ≥1 trụ mới đáng xét; không chạm trụ nào → loại. **Ngoại lệ học thuật (thể loại) đã BỎ** — arXiv/paper nay xét theo *relevance trụ cột + tính chuyển-giao* (chuyển-giao-được vs incrementalism leaderboard), không còn "là arXiv → pass". `ANALYSIS_PROMPT` bối cảnh đã sync theo. Đo trên 54 doc có nhãn tay: accuracy **70%→94%**, recall **53%→100%** (0 FN), precision 92% (3 FP). Benchmark 54-doc + nhãn nay ở **`backend/tests/eval/`** (tự chứa, không cần DB) — **chạy lại khi sửa `GATE_PROMPT`**, vì không có unit test nào bảo vệ *tiêu chí* gate (`test_gate_skipped.py` chỉ bảo vệ *cơ chế* fail-open):
  ```bash
  docker compose exec backend python -m tests.eval.harness          # offline, 0 đồng
  docker compose exec backend python -m tests.eval.harness --live    # đo lại thật, ~$0,10
  ```
  Gate đọc **`GATE_CONTENT_LIMIT` = 2000 ký tự đầu** content (`build_gate_prompt`), khác deep-analysis 6000 — đổi hằng số này thì **phải sinh lại fixture**, harness sẽ fail rõ ràng nếu quên. Bằng chứng đo gốc vẫn ở `openspec/changes/archive/2026-07-21-w4-gate-accuracy/eval/`, nhưng công cụ chạy thì **không** còn ở đó (script cũ bị xoá và chưa từng commit — đó là lý do có change `gate-benchmark-durability`).
- **Delivery qua email (thay Telegram, 21/07/2026 — change `refactor-telegram-to-gmail-transport`)**: transport là `EmailAdapter` (SMTP + Gmail App Password). **Alert tức thời đã BỎ HẲN** — gửi email 5 phút/lần chắc chắn bị xếp spam; tiêu chí `recommendations[role].urgency == "high"` nay là **tiêu chí xếp hạng số 1** của bản tin định kỳ. Env: `DELIVERY_ENABLED` (mặc định false, `main.py` mới thực sự đọc nó), `DELIVERY_CHANNEL`, `DELIVERY_DIGEST_HOUR` (giờ **VN**), `DELIVERY_DIGEST_DAYS` (mặc định `mon,thu`), `DELIVERY_DIGEST_LOOKBACK_HOURS` (**108**), `DELIVERY_MAX_ITEMS_PER_ROLE` (2), `DELIVERY_MAX_ITEMS_PER_EMAIL` (3), `SMTP_*`, `EMAIL_FROM*`, `DASHBOARD_BASE_URL` (link đọc chi tiết), `PUBLIC_API_BASE_URL` (**khác** — gốc link hủy nhận, trỏ backend). Subscription roles dùng 9 `ALLOWED_ROLES` trong `prompts.py`, KHÔNG phải 13 `target_roles` của Source. Email và chat **không nối vào nhau** (chốt 22/07): email là kênh push tin mức cao, chat chỉ sống trên dashboard.
- **Chat Q&A (M8, change `chatbot-qa` 22/07/2026)**: `POST /api/v1/chat` nhận `{question, history, insight_id?}`. Có `insight_id` → chế độ per-insight (context = insight fields + toàn bộ `raw_documents.normalized_content`); không có → chế độ toàn cục (server lọc + **xếp hạng HAI TẦNG** rồi cắt **top-K** thành index nén, đưa vào 1 lần gọi — **KHÔNG function-calling**, đo 22/07: cả 179 tin = 19.126 token = 1 lượt gọi, rẻ và nhanh hơn tool loop).
    - **Xếp hạng hai tầng, KHÔNG phải chỉ `score_for_role`**: tầng 1 là **độ liên quan** tới từ khoá câu hỏi, tầng 2 mới là độ quan trọng (`delivery_engine.score_for_role()`). Thứ tự này bắt buộc — `score_for_role` mù hoàn toàn với nội dung câu hỏi, và xếp chỉ bằng nó cho recall 42% (câu "mô hình mã nguồn mở" còn 11%), im lặng, vì model vẫn trả lời trôi chảy từ vài tin sót lại.
    - **Chi phí đã PHẲNG theo corpus nhờ `CHAT_INDEX_TOP_K`** (60): index chỉ mang top-K, nên corpus lớn lên không làm prompt to ra. Vì vậy lời khuyên cũ "hạ `CHAT_WINDOW_DAYS` xuống 90/30 khi corpus vượt ~1250 tin" **không còn cần cho chi phí** — chỉ hạ khi muốn *ưu tiên tin mới*, không phải để tiết kiệm token.
    - Env: `MAX_DAILY_CHAT_CALLS` (200), `CHAT_INDEX_TOP_K` (**60**; 0 = không cắt — đếm CẢ ô sâu), `CHAT_DEEP_SLOTS` (**3**), `CHAT_DEEP_INCLUDE_CONTENT` (true), `CHAT_WINDOW_DAYS` (0 = cả corpus), `INTENT_CLASSIFIER_ENABLED`, `INTENT_CLASSIFIER_MODEL_ID`, `EMBEDDING_MODEL_ID`, `CHAT_EMBEDDING_ENABLED`, `CHAT_THINKING_BUDGET` (**256**; 0 = tắt suy luận, −1 = để model tự quyết).
  - **HAI endpoint, MỘT pipeline (change `chat-streaming-sse`, 27/07/2026)**: `POST /api/v1/chat` blocking (giữ nguyên — client cũ, test, eval harness ④) và `POST /api/v1/chat/stream` SSE. Khác biệt duy nhất là `ChatService.answer(..., emit=...)`: có `emit` thì pipeline phát thêm `status`/`token` dọc đường. **Đừng tách thành hai nhánh logic** — grounding/xếp hạng/fail‑closed/budget phải dùng chung một đoạn code, không thì hai lối ra trôi khỏi nhau trong im lặng.
    - **Streaming KHÔNG chữa được độ trễ đầu, status mới chữa.** Đo thật 27/07: TTFT **8,0 / 12,9 / 34,9 / 36,7s** ở mode A (mode B đơn giản: 2,2s). Toàn bộ khoảng đó là **thinking — chưa có token nào để stream**. Cái lấp nó là hai sự kiện `status` đến ở giây ~0,7 và ~1,0. Vertex còn gộp chunk rất thô (một câu ~900 ký tự về trong **6** sự kiện `token`, chảy trong ~1,2s), nên hiệu ứng "gõ chữ" mờ nhạt; giá trị thật của change nằm ở status, không ở token. Đừng hứa "perceived <0.5s" như báo cáo To‑Be gợi ý.
    - **Provisional → commit**: token đã phát là **tạm**. `resolve_citations` + `enforce_grounding` chỉ chạy được trên câu HOÀN CHỈNH, nên sự kiện `commit` mang **toàn văn câu trả lời cuối** (không chỉ citations) và widget **THAY**, không nối thêm. Ca fail‑closed là ca text tạm hoàn toàn sai. ⚠️ `commit.answer` gần như **luôn** khác text đã stream kể cả khi không fail‑closed: `resolve_citations` chuẩn hoá khoảng trắng (`*   ` → `* `). Thấy bong bóng thụt lề nhẹ một lần lúc chốt là **đúng**, không phải lỗi render.
    - **Cổng chặn sentinel (`_SentinelGate`)** — lỗi do streaming đẻ ra: lượt mode B phát sentinel `[[NGOÀI_PHẠM_VI_BÀI]]` thành **đúng một token**, phát thẳng là người dùng thấy nó nhấp nháy. Bản blocking miễn nhiễm vì chỉ nhìn câu hoàn chỉnh. Cổng giữ token đầu chừng nào nó còn có thể là *tiền tố* của sentinel; câu bình thường lệch khỏi tiền tố ngay chunk đầu nên không bị trễ. Chỉ bật cho mode B (`hold_sentinel=True`).
    - **Budget sống sót khi client ngắt (D5)**: `answer_stream` chạy pipeline trong **task riêng** nên việc generator bị đóng không cắt ngang `finally` ghi `chat_logs`; `ChatStreamState.calls` cộng ngay từ chunk đầu (thời điểm tiền đã tiêu), không đợi hết luồng. Đo thật: ngắt sau token đầu ở giây 9,7 → `chat_logs` vẫn có dòng `('global', 1, 2, 9847)`. **Đây là chỗ rò dễ nhất của streaming — đừng "đơn giản hoá" bằng cách gọi `answer()` thẳng trong generator.**
    - **Lỗi đi bằng sự kiện `error`, không phải mã HTTP** — kể cả 429 hết quota. Cửa quota nằm SAU bộ định tuyến ý định (câu chào phải trả lời được khi budget cạn), nên trả 429 thật đòi chạy lại phần định tuyến ở route = nhân đôi logic. Câu meta phát đúng **một** `commit` mang preset, **không** stream token giả.
    - **Frontend**: `streamChat()` trong `api/chat.ts` dùng **fetch + ReadableStream** (`EventSource` chỉ biết GET, mà payload có `history`). Ranh giới khung SSE ≠ ranh giới chunk mạng — bộ đọc phải đệm tới `\n\n`, và `data` luôn là JSON một dòng (token chứa `\n` sẽ cắt khung nếu dán thô). Text tạm nằm ở state `pending` **ngoài** `threads`: chỉ câu đã chốt mới nhập luồng, nhờ vậy phần dở không bao giờ lọt vào `history` lượt sau. Đổi scope giữa luồng → `abort()` (D6). Nút Gửi disabled khi đang stream (chống thundering herd). Test: `ChatWidget.streaming.test.tsx`, `api/__tests__/chatStream.test.ts`.
    - ⚠️ **Khi deploy sau reverse proxy**: nginx **đệm response theo mặc định** → SSE về thành một cục ở cuối, mất sạch streaming mà **không có lỗi nào bắn ra**. Route đã gửi `X-Accel-Buffering: no`; nếu proxy không tôn trọng header thì cần `proxy_buffering off;` + `proxy_read_timeout` đủ dài (câu nặng ~40s) cho location `/api/v1/chat/stream`. Môi trường local hiện tại không qua proxy nên chưa gặp.
  - **Citation do server cấp phát**: prompt KHÔNG chứa UUID, model chỉ trả text thuần có marker `[n]`, server tra bảng `n → insight_id`. Chống bịa bằng **cấu trúc**, không phải hậu kiểm — đừng "tiện tay" thêm id vào index.
  - **`n` là SỐ INDEX, không phải vị trí trong mảng `citations`** (change `chat-citation-integrity`, 27/07/2026). Backend đánh số theo index (1..60); `citations[]` chỉ nén những tin được trích (1..k, k≤5). Widget cũ tra `citations[n-1]` — trộn hai hệ quy chiếu, và **chỉ đúng khi model trích liền mạch từ [1]**, điều nó thường làm chỉ vì prompt dặn "tin ở đầu danh sách đáng chọn hơn". Tức là bất biến dựa vào **thói quen của model**, và nó vỡ ngay khi model bỏ qua một tin ở giữa (`[1][2][4]`). Nay `Citation` mang trường **`n`** tường minh; frontend giải bằng `citations.find(c => c.n === n)`. **Đừng "tối ưu" về phép tính chỉ số.**
    - Marker trong answer **giữ nguyên số**, server KHÔNG đánh số lại (đánh lại là *viết lại* output của model, và đá nhau khi câu trả lời tự nhắc "tin số 3 ở trên"). Danh sách nguồn dưới bong bóng vì thế hiện `[3][7][12]` — **khớp marker inline**, không phải `[1][2][3]`.
    - Đây là lỗi **sống ở khe giữa hai tầng**: `test_resolve_citations_maps_markers_in_order` khẳng định `[2]→B, [1]→A` và **xanh** ở backend, trong khi chính ca đó làm widget trỏ sai cả hai. Test một bên ranh giới không bảo vệ được ranh giới — lưới thật là `frontend/src/components/__tests__/chatAnswer.boundary.test.ts` (6 dãy marker, kèm một test đối chứng chứng minh cách cũ sai 5/6).
    - Marker không liền mạch từ 1 được log mức **DEBUG** ở `resolve_citations` — tín hiệu sớm cho việc xếp hạng đặt tin lệch vào top. Quan sát, không phải lỗi.
  - **Tín hiệu THỨ BA: tương đồng mức ĐOẠN thân bài** (change `chat-chunk-retrieval`, 28/07/2026). RRF nay là `1/(60+r_lex) + 1/(60+r_vec) + 1/(60+r_chunk)`. Lý do: hai tín hiệu cũ đều đọc **bản phân tích do Gemini viết** (`_relevance` soi 5 field, `build_embedding_text` embed đúng 5 field đó), phủ **4%** từ vựng thân bài — nên hỏi bằng định danh chỉ có trong bài (`SquashFS`, `SPDX`, `HMAC-SHA256`) thì không tín hiệu nào biết bài đó tồn tại. Đo 28/07 trên 15 kịch bản `detail_discovery`: recall@5 **0,667 → 1,000**, hạng xấu nhất 29 → 4; toàn bộ 98 câu RS: r@5 0,832 → 0,900, r@60 0,975 → 0,968.
    - **Một suất Ô SÂU dành cho tin có đoạn khớp NHẤT toàn corpus** (`_best_chunk_match`, chỉ nhận **hạng đoạn = 1**, hoà thì bỏ qua; đứng sau `referenced_insight_ids`, trước phần lấp theo thứ hạng tổng). Vì sao cần: tầng đoạn chữa **truy hồi** nhưng không chữa **bằng chứng** — bài hạng 4–5 vào prompt chỉ dưới dạng dòng index nén của phần *phân tích*, đúng chỗ KHÔNG chứa định danh được hỏi, nên model từ chối dù bài đúng đã nằm trong context. Đo 28/07: `det-squashfs` (hạng tổng 4) và `det-spdx-cyclonedx` (hạng 5) đều có hạng đoạn 1 → AnsRel **0,00 → 1,00**; nhóm `detail_discovery` **12/15 → 15/15** câu trả lời được, AnsRel 0,73 → **0,93**. Đây KHÔNG phải heuristic đoán ý định câu hỏi (thứ repo này đã trả giá nhiều lần) mà là một **sự kiện đo được**; và ranh giới spec vẫn nguyên — nội dung vẫn đi qua ô sâu, chỉ đổi tin nào được rót. **Không** áp cho chế độ mở rộng (ô sâu duy nhất ở đó là bài đang xem).
    - **ĐOẠN XẾP HẠNG, INSIGHT TRÍCH DẪN** — bất biến quan trọng nhất. Đoạn KHÔNG BAO GIỜ là đích của marker `[n]`, không bao giờ vào prompt như một mục nguồn đánh số riêng. Nội dung vào câu trả lời vẫn đến từ **ô sâu** của `chat-context-depth`. Cho đoạn thành nguồn trích dẫn là dựng lại cái bẫy "hai hệ quy chiếu cho `n`" của `chat-citation-integrity`, ở quy mô lớn hơn (bài 5 đoạn ⇒ 5 số cho một nguồn). Khoá bằng `tests/test_chunk_not_citable.py`.
    - **Insight nhận hạng của ĐOẠN TỐT NHẤT** (`min`), không phải trung bình — trung bình phạt bài dài vì những đoạn lạc đề mà chính nó không chọn có.
    - **Tin chưa có đoạn mượn `rank_vector` của chính nó**; nhưng **cả lượt không có tín hiệu đoạn thì BỎ HẲN số hạng thứ ba**, không phải cho mượn. Mượn ở mức toàn lượt sẽ nhân đôi trọng số tầng vector và cho một thứ tự KHÁC bản hai tín hiệu — tức là một đường xếp hạng thứ ba xuất hiện đúng lúc hệ thống đang hỏng. Suy giảm êm nghĩa là **trùng khít**.
    - ⚠️ **Câu RỖNG TỪ KHOÁ phải tắt CẢ tầng đoạn, không chỉ tầng vector.** Bỏ sót đúng dòng này thì `rank-generic` ("Có gì mới không?") tụt recall@60 1,00 → 0,00 — tin CISA vá khẩn rơi xuống **hạng 109/179**, văng khỏi cả index. Lượt mô phỏng ngoài `_rank` KHÔNG thấy lỗi này; chỉ RS harness chạy qua đúng `_rank` production mới lộ.
    - **Lọc thô đẩy xuống SQL** (`ORDER BY embedding <=>` trên HNSW, `DEFAULT_CHUNK_LIMIT=300`) — đây là **cắt lấy ứng viên**, KHÔNG phải ngưỡng similarity. Đo 28/07: **13ms/câu** (ngưỡng mở lại thiết kế là 0,5s), ~125 tin có thứ hạng đoạn, rộng hơn `chat_index_top_k`=60 một quãng an toàn.
    - **RS harness vẫn MIỄN PHÍ và offline** nhờ đông lạnh **THỨ HẠNG**, không phải vector đoạn (`chat_chunk_ranks.jsonl`, 0,6MB): đông lạnh vector buộc harness tự dựng lại phép `ORDER BY <=>` + gộp `min` bằng code thứ hai — đúng chế độ hỏng "hai đường tính khác nhau, không có gì báo lỗi". Thêm kịch bản / đổi hằng số chunk ⇒ `build_fixture_chat --top-up`. File mang **dòng meta dấu vân tay** (số đoạn + hằng số chunk + model embedding) và `load_chunk_ranks` **NỔ** nếu lệch — không có nó thì đổi hằng số chunk rồi `--redo` sẽ để fixture mốc mà mọi con số vẫn trông bình thường.
    - ⚠️ **Bảng đoạn rỗng = suy giảm IM LẶNG**: `alembic downgrade -1` DROP TABLE nên xoá sạch dữ liệu, và chat chỉ lặng lẽ tụt về 2 tín hiệu. Sau mỗi round-trip migration **phải** chạy lại `chunk_documents`. `_chunk_ranks` nay log WARNING khi bảng rỗng để biến nó thành lỗi nghe được.
    - **Hằng số chunk là hợp đồng embedding** (`app/ai/chunking.py`: 2000/2400/300 ký tự): đổi ⇒ **bắt buộc** `chunk_documents --redo` + sinh lại fixture, vì trộn hai họ vector làm cosine lệch mà **không có gì báo lỗi**.
    - **`purge_expired` phải xoá đoạn TƯỜNG MINH**: bảng có `ON DELETE CASCADE`, nhưng purge không xoá hàng `raw_documents` — nó chỉ rỗng hoá `normalized_content`, nên cascade không bắn và đoạn sống sót cùng nội dung đã bị yêu cầu xoá.
    - Lượt embed đoạn **KHÔNG** tính vào `MAX_DAILY_CHAT_CALLS`/`MAX_DAILY_ANALYSIS` (cùng lý do với embed insight).
  - **Truy hồi LAI: RRF(vector, lexical), KHÔNG ngưỡng** (change `chat-hybrid-retrieval`, 27/07/2026). Tầng độ‑liên‑quan của `_rank` trộn **thứ hạng** lexical (`_relevance`, khớp biên từ) với **thứ hạng** vector (cosine embedding) bằng `1/(60 + rank)`, rồi mới tới khoá phụ `score_for_role`, rồi cắt `chat_index_top_k`. Chữa chế độ hỏng còn lại của keyword thuần: hỏi "DevOps cần chú ý gì" mà tin đúng là checklist Kubernetes **không chứa chữ DevOps** → lexical đẩy xuống hạng 47, vector kéo lên hạng 1. Đo 27/07 trên 42 câu RS: recall@60 0,964 → 0,970, **recall@5 0,780 → 0,859**, không câu nào tụt.
    - **RRF chứ không cộng điểm thô**: cosine và số‑từ‑khoá‑khớp không cùng thang đo; chuẩn hoá chúng về một thang là bịa ra một hằng số không ai kiểm được. RRF chỉ đọc thứ hạng nên miễn nhiễm. `RRF_K = 60` trùng số với `chat_index_top_k` là **ngẫu nhiên** — hằng số làm phẳng ≠ số tin vào prompt, đổi K không được đổi nó.
    - **Giữ CẢ lexical, không thay hẳn bằng vector**: vector kém ở khớp CHÍNH XÁC (tên model, mã CVE, số phiên bản) — đúng loại câu hỏi hay gặp ở đây.
    - **KHÔNG ngưỡng similarity.** Vector chỉ để xếp hạng *tốt hơn*, không để lọc; vẫn cắt top‑K nên tập ứng viên **không bao giờ rỗng** vì "không tin nào đủ giống". Ngưỡng 0,65 của báo cáo To‑Be bị loại vì nó tái sinh đúng cái chế độ hỏng change này chữa.
    - **Câu hỏi RỖNG TỪ KHOÁ thì TẮT tầng vector** (`if not _question_terms(question)`). "Có gì mới không?" không có chủ đề để mà giống ⇒ embedding của nó là **nhiễu**, và nhiễu đó đè tầng độ quan trọng: đo 27/07, bỏ cổng này thì `rank-generic` tụt recall@5 **1,00 → 0,00**, tin CISA vá khẩn rơi xuống hạng 23. ⚠️ Điều kiện là *câu hỏi rỗng từ khoá*, KHÔNG phải *không tin nào khớp từ khoá* — câu tiếng Việt hỏi corpus tiếng Anh cho `_relevance = 0` ở mọi tin nhưng vẫn có nội dung ngữ nghĩa thật, đó đúng là ca vector sinh ra để cứu.
    - **Suy giảm êm là bất biến, không phải nỗ lực**: embed câu hỏi lỗi / `chat_embedding_enabled=false` → `query_vector=None` → thứ tự **trùng khít** bản lexical cũ (RRF trên một tín hiệu là hàm đơn điệu của chính thứ hạng đó). Chat không bao giờ 500 vì embedding. Tin `embedding IS NULL` **mượn thứ hạng lexical của chính nó** cho số hạng vector — bỏ hẳn số hạng đó đi là hình phạt ngầm nặng (tin chỉ được nửa điểm, thua cả khi khớp từ khoá chính xác, và trong cửa sổ backfill thành thiên lệch hệ thống); cho cosine = 0 thì sai hướng khác (0 là thứ hạng THẬT ở cuối bảng = biến "chưa biết" thành "chắc chắn không liên quan").
    - **Vòng đời embedding**: `text-multilingual-embedding-002` qua Vertex, **768 chiều**, chốt cứng vào `insights.embedding vector(768)` (migration 012). Sinh khi publish trong `AnalyzerService._attach_embedding` (lỗi → NULL + WARNING, **không** chặn tạo insight); vá bằng `python -m app.scripts.embed_insights` (idempotent, chỉ đụng hàng NULL). Text embed dựng ở **một chỗ** — `app/ai/embedding.py::build_embedding_text` (`title + signal + so_what + summary_short + topics`); đổi nó hoặc đổi model ⇒ phải `embed_insights --redo`, vì trộn hai họ vector trong một cột làm cosine lệch mà **không có gì báo lỗi**.
    - **Lượt embed KHÔNG tính vào `MAX_DAILY_CHAT_CALLS` / `MAX_DAILY_ANALYSIS`** — cùng lý do với bộ phân loại ý định tầng 2: hai bộ đếm đó canh budget lượt sinh văn bản ~19k token; lượt embed ~30–200 token trên model rẻ hơn vài bậc.
    - **Xếp hạng vector tính trong Python, không phải `ORDER BY embedding <=>` trong SQL** — để `_rank` là hàm THUẦN cho RS harness đo offline/miễn phí. Index HNSW ở migration 012 là hạ tầng dựng sẵn cho lúc corpus đủ lớn phải lọc thô trong SQL. Cái giá hiện tại: mỗi câu hỏi toàn cục kéo thêm ~550KB vector từ Postgres.
    - **Sửa `_rank`/embedding ⇒ BẮT BUỘC chạy lại RS harness VÀ chốt lại baseline kèm lý do**, và chạy lại `chat_answer_harness --live` (đổi context = đổi câu trả lời). Thêm kịch bản RS ⇒ chạy lại `build_fixture_chat` để sinh vector câu hỏi, không thì harness **nổ** chứ không lặng lẽ đo lối lexical.
    - **Giới hạn đã đo — ⑥ không chữa hết**: `rank-eol-khai-tu` ("công nghệ nào sắp bị *khai tử*") đứng yên ở recall@60 0,50; embedding bắt được sắc thái "phải chuyển đổi" nhưng không nối được thành ngữ đó với "end of support". Kịch bản giữ lại **dù đỏ** làm mốc cho rerank cross‑encoder — **đừng chữa bằng cách sửa câu hỏi cho gần chữ trong tin hơn**, làm thế là xoá phép đo. Chi tiết: `openspec/changes/chat-hybrid-retrieval/measurement.md`.
  - **Chat KHÔNG dùng `response_mime_type`/`response_schema`** (bài học `gemini-structured-output`: output dài + schema = runaway → JSON vỡ).
  - **⚠️ Đơn vị budget khác nhau**: `MAX_DAILY_ANALYSIS` đếm *tài liệu* (1 tài liệu = 2 lượt gọi model), `MAX_DAILY_CHAT_CALLS` đếm *lượt gọi*. Counter chat là `SUM(chat_logs.model_calls)` theo ngày UTC — bảng log cũng chính là counter.
  - **Thinking tokens chi phối chi phí/độ trễ — nay ĐÃ GHÌM** (change `chat-latency-thinking-budget`, 27/07/2026). `CHAT_THINKING_BUDGET` = **256**, áp CHỈ cho đường chat. Kết quả: độ trễ trung vị **4,7s** (1 lượt gọi) và **6,9s** (mở rộng, 2 lượt), thinking 1.877–2.752 → **216–253** token/câu, tiền phần thinking giảm ~8 lần.
    - **Nguyên nhân độ trễ KHÔNG phải kích thước prompt** — đây là điều đo ra ngược với trực giác. Prompt tầm thường (534 token vào, 10 token ra, "trả lời đúng một từ") vẫn mất **10,3s** vì model nghĩ 1.416 token. Còn cắt ngữ cảnh 6.537 → 1.540 token (−76%) chỉ đưa 17,4s xuống 11,6s (−33%). **⇒ ĐỪNG cắt `CHAT_INDEX_TOP_K` để tìm tốc độ** — nó trả bằng recall mà mua được rất ít. Retrieval cả cụm (embed + DB 0,2s + `_rank` 0,03s) chỉ ~0,5s khi kết nối ẤM; ~90% độ trễ nằm ở lượt gọi model.
    - **Chi phí này TỪNG VÔ HÌNH**: `google-genai==0.8.0` luôn trả `thoughts_token_count` rỗng, nên `usage_metadata` nhìn như thinking = 0. Chỉ lộ ra vì `total_token_count` lệch so với `prompt + candidates`. Nay ghi thẳng vào `chat_logs.thinking_tokens` (migration 013) để không bao giờ ẩn lại. **`NULL` ≠ `0`**: NULL = nhà cung cấp không báo cáo, 0 = đã ghìm và model tuân thủ — đừng gộp.
    - **SDK dừng ở `google-genai==1.75.0`, ĐỪNG lên 2.x**: từ 2.0 SDK đòi `pydantic>=2.12.5`, đá nhau với `pydantic==2.9.2` đang pin (`ResolutionImpossible`). 1.75.0 là bản cuối nhánh 1.x, chỉ đòi `pydantic>=2.9.0`, và đã có đủ `ThinkingConfig(thinking_budget=...)` + `thoughts_token_count` ⇒ lên 2.x không mua thêm gì mà kéo theo nâng cả pydantic/FastAPI.
    - **Cấu hình dựng ở MỘT chỗ** (`_chat_generation_config`) dùng chung cho `chat()` và `chat_stream()`. Đặt riêng cho một bên là để hai lối ra trả lời khác nhau **im lặng** — mà `chat_answer_harness` chỉ đi lối blocking, nên cổng chất lượng sẽ gác một cấu hình người dùng không hề chạy. Có test `inspect.getsource` khoá điều này.
    - **`gate_analyze`/`analyze`/`classify_intent` KHÔNG bị ghìm** — tác vụ nền, độ trễ không nằm trên đường phục vụ người dùng; đụng vào là phải chạy lại benchmark gate 54 doc.
    - **LUẬT CHỈNH BUDGET: chỉ nâng, không hạ ngưỡng.** `--live` cho Faith < 0,95 hoặc CitPrec < 1,00 ⇒ nâng 256 → 512 → 1024. Đo 27/07 ở 256: Faith 0,99 · CitPrec 1,00 · AnsRel 0,93→**0,91** (trong dung sai 0,05 nhưng **cùng chiều** với việc cắt suy luận — theo dõi, đừng đọc như nhiễu). `-1` = trả về hành vi cũ để so sánh.
    - **Còn 2/62 câu vượt 8s** (câu tóm tắt tổng hợp, 9,5s và 8,8s). ⚠️ **SỬA 28/07/2026 — con số "embed 1,4s, dư địa lớn nhất còn lại" là SAI, đo trên kết nối LẠNH.** Đo lại 3 lần liên tiếp cùng tiến trình: lần đầu 1,67s, hai lần sau **0,37s** — 1,3s kia là bắt tay TLS/auth, mà production dùng `get_chat_client()` **singleton** nên chỉ trả một lần cho cả vòng đời process. Embed thật ≈ **11% TTFT**, không phải 30%, và cache nó gần như không mua được gì. Bất kỳ phép đo độ trễ chat nào tạo `GeminiClient()` mới mỗi câu đều **thổi phồng** kết quả ~1,3s/câu — làm ấm kết nối trước khi đo. Số đo đầy đủ: `openspec/changes/chat-latency-thinking-budget/measurement.md` (bản cũ) và `chat-context-depth/measurement.md` (bản sửa).
  - **Chat KHÔNG BAO GIỜ trả câu trả lời dở dang (25/07/2026)**: cách cũ dán `_(Câu trả lời bị cắt vì quá dài — bạn thử hỏi hẹp hơn nhé.)_` vào cuối đoạn đứt giữa từ — tức giao cho người dùng một câu trả lời **thiếu vế sau**, mà vế thiếu thường là khuyến nghị/rủi ro. Nay `GeminiClient.chat()` gặp `MAX_TOKENS` thì **hỏi lại** với `_CONCISE_RETRY_DIRECTIVE` (gộp ý, tối đa 5 gạch đầu dòng, *đủ ý* chứ không cắt phạm vi); lượt hỏi lại **có tính** vào `calls` trả về nên budget vẫn khớp. Nếu hỏi lại vẫn cắt → `_trim_to_last_sentence()` lùi về câu hoàn chỉnh cuối, **không** dán lời xin lỗi. `CHAT_MAX_OUTPUT_TOKENS` 4096 → **8192** (chỉ tính tiền theo token thực sinh nên trần cao không đắt hơn cho câu ngắn). Test: `tests/test_chat_truncation.py`.
  - **`FinishReason` là enum CHUỖI**: `.value` trả `'MAX_TOKENS'`, KHÔNG phải `2`. Cách viết cũ `== 2` trong `analyze()` khiến cảnh báo cắt chưa từng bắn — đã sửa bằng helper `_is_truncated()` dùng chung.
  - **Fast‑path chào hỏi/meta trả preset, 0 gọi model** (change `chat-intent-router`, 24/07/2026): `ChatService.answer()` chạy `classify_intent()` (deterministic, trong `services/chat_intent.py`) **TRƯỚC cửa quota**. Câu chỉ là chào/meta/cảm ơn ("xin chào", "bạn làm được gì?", "cảm ơn") → trả câu định sẵn trong `INTENT_PRESETS`, `mode="meta"`, `citations=[]`, **0 lượt gọi model**, ghi `chat_logs` với `model_calls=0`. Vì 0‑call nên nó **không tính quota VÀ không bị quota chặn** — chào vẫn trả lời được khi `max_daily_chat_calls` đã cạn; câu thật thì vẫn 429. Phân loại thiên **fall‑through**: lưỡng lự thì đi pipeline. Test: `tests/test_chat_intent_router.py`. `STOPWORDS` nay ở `services/chat_service_terms.py` (dùng chung `chat_service` + `chat_intent`, tránh import vòng).
  - **Bộ lọc ý định nay có HAI TẦNG (25/07/2026)** — `ChatService._route_intent()`:
    - **Tầng 1 `route_intent()`** (tất định, 6µs, 0đ) trả **ba trạng thái**: nhóm preset / `None` (câu tra cứu) / `AMBIGUOUS`. Quyết **96,4%** số câu.
    - **Tầng 2 `GeminiClient.classify_intent()`** — `gemini-2.5-flash-lite`, chỉ chạy khi tầng 1 trả `AMBIGUOUS` (**3,6%** câu).
    - **ĐỪNG giao hết cho model** (đo 25/07/2026, 84 ca nhãn tay): sàn round‑trip của flash‑lite là **1.433–1.685 ms** *kể cả với prompt rỗng và 1 token output* — đó là mạng + TTFT, không cắt được bằng cách chọn model nhỏ hơn. Giao hết = cộng ~1,45s vào **mọi** câu tra cứu thật (15,9s → 17,4s), mà precision lại **tụt còn 91,5%** so với 97,6% của luật (nó gạt nhầm "cảm ơn vì tin về mã nguồn mở" → `thanks`). Bộ lai đạt **precision 100% / recall 97,7% / đúng 98,8%**.
    - **Luật hồi chỉ là của TẦNG 1, không nhường model**: `_ANAPHORA_TOKENS` (`nó`, `này`, `cái`, `bài`…) không kèm tự‑quy‑chiếu (`bạn`/`bot`/`trợ lý`) ⇒ câu tra cứu. flash‑lite trả `capability` cho "nó là ai" **ngay cả khi prompt nêu thẳng ca đó là Q**.
    - `_CAPABILITY_CONTENT_TOKENS` **suy ra tự động** từ `_CAPABILITY_PHRASES`. Trước đó 14/17 cụm là **code chết** vì cổng "phần còn lại rỗng" chạy trước — suy ra tự động để lỗi đó không tái sinh khi thêm cụm.
    - Lượt gọi tầng 2 **KHÔNG** tính vào `model_calls`: bộ đếm đó canh budget lượt trả lời đắt (~19k token trên `gemini-2.5-flash`). Tầng 2 là ~259 token vào + 1 token ra trên model rẻ hơn một bậc ≈ **$0,026/1000 câu**. Trộn chung = để lượt gọi rẻ bào mòn budget đắt.
    - Tắt tầng 2: `INTENT_CLASSIFIER_ENABLED=false` → lưỡng lự rơi về pipeline. Test: `tests/test_chat_intent_hybrid.py` (có cổng chặn hồi quy giữ tỉ lệ chạm tầng 2 ≤ 10%).
  - **BA SCOPE + auto‑fallback (change `chat-scope-routing`, 25/07/2026)**: *Bài đang xem* (B) và *Toàn hệ thống* (A) là hai lựa chọn người dùng thấy; *Mở rộng* (B + toàn cục) **không phải nút bấm** — nó sinh ra TỰ ĐỘNG khi mode B bí.
    - **Cơ chế = sentinel + lượt gọi thứ 2, KHÔNG classifier**: prompt mode B dặn model in đúng một dòng `OUT_OF_SCOPE_SENTINEL` (`[[NGOÀI_PHẠM_VI_BÀI]]`, hằng số trong `prompts.py`) khi câu hỏi không trả lời được từ bài. Server dò sentinel → dựng context mở rộng → gọi lần 2 → `mode="expanded"`. Tín hiệu ngoài‑phạm‑vi là **byproduct của chính lượt trả lời B**, không tốn lượt gọi phân loại riêng. Không `response_schema` (bài học `gemini-structured-output`).
    - **Dò sentinel PHẢI chạy trước `enforce_grounding`**: sentinel không mang marker `[n]` nào, nên để grounding chạy trước thì nó bị thay bằng `INSUFFICIENT_GROUNDS_MESSAGE` và tín hiệu mất sạch.
    - **Sentinel phát DÈ DẶT** — bias NGƯỢC với `chat-intent-router`: ở đó gạt nhầm câu thật mới là hỏng nặng; ở đây **mở nhầm** mới là hỏng nặng (tốn gấp đôi lượt gọi + độ trễ), còn thiếu mở rộng thì người dùng vẫn còn badge chuyển phạm vi làm lưới. `is_out_of_scope_answer()` vì thế chỉ nhận khi sentinel là **toàn bộ** câu trả lời — vừa trả lời vừa kèm sentinel = trả lời được.
    - **Đánh số liên tục qua hai khối**: lượt mở rộng mang cả bài đang xem (giữ `[1]`) lẫn index toàn cục (`build_index_block(start=2)`), và bài đang xem bị **loại khỏi** index toàn cục — không thì cùng một tin có hai số và citation trỏ trùng.
    - **Câu mở rộng tốn ĐÚNG 2 BƯỚC** — đây chính là chỗ dùng của `MAX_MODEL_CALLS_PER_QUESTION=2` vốn để dành. ⚠️ **BƯỚC ≠ LƯỢT TÍNH TIỀN** (sửa 25/07): retry chống-cắt của `chat-answer-completeness` làm một bước có thể tốn 2 lượt. Khi hai nghĩa còn dùng chung một bộ đếm, đo được hai lỗi thật: (A) mở rộng + lượt 2 bị cắt → 3 lượt, vượt chính cái trần spec tuyên bố; (B) lượt B bị cắt → hỏi lại → bản hỏi lại phát sentinel → mở rộng bị trần chặn → `RuntimeError` thoát ra thành **HTTP 500**. Nay `_steps_used` chịu trần, `_calls_used` chỉ để ghi log/budget ⇒ tối đa 4 lượt tính tiền/câu. **Trần chống-tool-loop phải đếm bước lập luận; budget phải đếm tiền** — đừng gộp lại. Đo thật 25/07 (bài `OWASP/Nettacker`): in‑scope 6/6 → `insight`, 1 lượt, 2,1–5,7s; out‑of‑scope 5/5 → `expanded`, 2 lượt, 6,9–18,7s. **Sentinel giả 0/6 (0%)**. Độ trễ mở rộng ≈ **3,2×** — đó là thứ `chat-streaming-sse` (⑤) sẽ che, không phải lý do bỏ fallback.
    - **v1 mở rộng bằng keyword‑rank**: câu diễn đạt lệch từ khoá (sa thải vs *layoff*) vẫn có thể sót; recall ngữ nghĩa đầy đủ chờ `chat-hybrid-retrieval` (⑥).
    - **Badge phạm vi HAI CHIỀU thay chip bỏ‑ngữ‑cảnh một chiều của `chat-context-isolation`**: chip cũ chỉ đi được bài → toàn cục, muốn quay lại bài phải điều hướng. Badge (`styles.scopeBar`) hiện "Phạm vi: Bài đang xem / Toàn hệ thống" và chuyển được cả hai chiều tại chỗ. **Chip cũ KHÔNG còn** — đừng tìm `.chip`/aria‑label "Bỏ ngữ cảnh…" nữa. Chuyển scope vẫn = đổi `scopeKey` = đổi luồng (cô lập của ①). Test: `tests/test_chat_scope_routing.py` (backend), `ChatWidget.scope.test.tsx` (frontend).
  - **Benchmark xếp hạng là lưới DUY NHẤT bắt hồi quy `_rank`** (change `chat-rank-stability`, 27/07/2026). `_rank()` quyết định tin nào lọt vào index; cắt sai ở đây thì model **không bao giờ nhìn thấy** tin đúng mà **vẫn trả lời trôi chảy** từ phần còn lại — `chatbot-qa` 4b.2 đo được recall 42%, riêng câu "mô hình mã nguồn mở" còn 11%. Bốn file test chat cũ đều bảo vệ *cơ chế*, không file nào bảo vệ *chất lượng xếp hạng*.
    ```bash
    docker compose exec backend python -m tests.eval.chat_rank_harness                    # 0 đồng, tức thì
    docker compose exec backend python -m tests.eval.chat_rank_harness --freeze-baseline  # chốt lại, CÓ CHỦ ĐÍCH
    ```
    - **Miễn phí và chạy trong `pytest` mặc định** — khác hẳn hai harness kia. Thứ nó đo là **code của chúng ta**, không phải phán đoán của model, nên không có `--live`, không tốn đồng nào, tất định. Client model bị tiêm `_NoModel` **nổ khi bị chạm tới**: bất biến "miễn phí" là cấu trúc, không phải lời hứa.
    - ⚠️ **Đừng đọc recall@60 như thước đo chính — nó bão hoà ở 1,000**. `must_have` được chọn vì hiển nhiên liên quan ⇒ khớp từ khoá ⇒ tầng 1 của `_rank` đẩy lên đầu ⇒ luôn lọt top-60/179. Đại lượng nhạy là **recall@5** (5 = trần "TỐI ĐA 5 tin" trong `CHAT_SYSTEM_PROMPT`) và cột **hạng xấu nhất**. Baseline 27/07: recall@60 **1,000** nhưng recall@5 chỉ **0,812**, phân biệt rõ theo nhóm (`ascii_short` 0,00 · `role_trap` 0,25 · `open_model` 0,50). Con số 42% của 4b.2 đo khi xếp hạng **chỉ có** `score_for_role` — chế độ đó không còn.
    - **BẮT BUỘC chạy lại** khi sửa `_rank`, `_relevance`, `_question_terms`, `_roles_in_question`, `STOPWORDS`, `score_for_role`/`role_urgency`/`has_practical_indicator`, hoặc `chat_index_top_k` (harness đọc K từ settings, không chép cứng).
  - **`_roles_in_question` khớp theo BIÊN TỪ — đừng "tối ưu" về `in` chuỗi**: bản cũ `role.lower() in question.lower()` cho `"tin về device IoT mới"` → `['Dev']` và `"DevOps cần chú ý gì"` → `['Dev']` (`DevOps` còn thuộc taxonomy `Source.target_roles`, **không** thuộc `ALLOWED_ROLES` — sai hai lần). Ở công ty có trụ cột IoT/Smart Home thì `device` xuất hiện dày đặc. Hậu quả **nặng hơn** `_relevance` sai: `_relevance` lệch điểm một tin, còn nhận nhầm vai trò **đổi cả trục xếp hạng** của toàn danh sách, và kéo theo `empty_roles` ⇒ bot tuyên bố sai "hệ thống không có tin nào cho vai trò Dev" cho câu chưa từng nhắc `Dev`. Phải so **dãy token liên tiếp** chứ không so tập hợp, vì vai trò là cụm nhiều từ (`Data Analyst` 2 token, `Người dùng phổ thông` 4 token). Test: `tests/test_chat_role_axis.py` (quay về bản cũ ⇒ 4 test đỏ) + `test_device_question_does_not_claim_anything_about_dev_role`. Trục đã chọn được ghi log mức **DEBUG** ở `_answer_global` — quan sát, không phải lỗi. **Chưa có bảng đồng nghĩa vai trò** (design D6): "developer" hiện KHÔNG kích hoạt trục `Dev`, và đó là suy giảm êm có chủ đích — đoán sai đồng nghĩa sẽ đổi trục xếp hạng một cách im lặng, đúng loại lỗi vừa phải sửa.
  - **Eval chất lượng câu trả lời là lưới DUY NHẤT bắt hồi quy Faithfulness / Answer‑Relevance** (change `chat-eval-quality-gate`, 27/07/2026). Không unit test nào bảo vệ *chất lượng* câu trả lời — chúng chỉ bảo vệ *cơ chế* (grounding, truncation, scope). Hồi quy chất lượng lại vô hình trong production: câu trả lời sai vẫn đọc rất trôi chảy. Bộ đo ở `backend/tests/eval/chat_answer_harness.py`, 56 kịch bản gán nhãn tay (15 mode B · 28 toàn cục · 13 mở rộng), fixture tự chứa (`chat_corpus.jsonl` 179 tin + `chat_anchors.jsonl` bài gốc của anchor + `chat_scenarios.jsonl`), sinh lại bằng `python -m tests.eval.build_fixture_chat`.
    ```bash
    docker compose exec backend python -m tests.eval.chat_answer_harness            # offline, 0 đồng, chấm lại snapshot
    docker compose exec backend python -m tests.eval.chat_answer_harness --live      # đo thật, ~$0,3–0,5, ~15 phút
    docker compose exec backend python -m tests.eval.chat_answer_harness --only exp-kasa-to-lambda   # đo lại một ca lẻ
    docker compose exec backend python -m pytest tests/eval/ -q                      # live bị skip mặc định
    ```
    - **Hai cách chấm, cố ý KHÔNG đồng nhất**: (a) **LLM‑judge** cho Faithfulness + Answer Relevance — không có bản tất định đáng tin, so chuỗi bỏ sót diễn giải khác chữ; (b) **thuần cấu trúc, 0 lượt gọi model** cho Citation Precision — nó là quan hệ `marker → mapping → insight`, đo được không cần model.
    - **Citation Precision phải đo trên câu trả lời THÔ, trước `resolve_citations`**: hàm đó âm thầm xoá mọi marker ngoài bảng ánh xạ, nên đo sau nó thì điểm **luôn** 1,00 và bộ đo thành đồ trang trí. Harness bắt raw answer bằng cách bọc `chat_service.resolve_citations`. Khoá bằng `test_citation_precision_measured_before_grounding_strips_markers`.
    - **Ngưỡng gate**: Faithfulness **≥ 0,95** và Citation Precision **= 1,00** (cứng, theo báo cáo To‑Be); Answer Relevance đóng băng baseline + dung sai 0,05 — báo cáo chỉ chốt số cho hai cạnh đầu. Baseline 27/07/2026 (commit `a00fe2e`): **Faith 0,991 · AnsRel 0,922 · CitPrec 1,000**, từ chối đúng 5/5, lệch mode 0/56.
    - **BẮT BUỘC chạy lại `--live`** khi sửa `CHAT_SYSTEM_PROMPT`, prompt mode B / `_SCOPE_RULE` / `OUT_OF_SCOPE_SENTINEL`, `enforce_grounding`/`resolve_citations`, `_rank`/`chat_index_top_k`, hay đổi model/SDK. Chốt lại baseline là **hành động có chủ đích kèm lý do**, không phải thao tác để test chuyển xanh.
    - **Nhóm `absent`/`role_empty` cố ý có AnsRel thấp** và bị loại khỏi trung bình: câu trả lời đúng ở đó là *từ chối*, mà từ chối thì theo định nghĩa không "giải quyết" câu hỏi. Chúng được đo bằng cột `từ chối đúng`. **Đừng "chữa" điểm nhóm đó** — chữa nghĩa là dạy bot bịa.
    - **Nhãn tay sai thì sửa nhãn, đừng sửa ngưỡng**: đo 27/07 có đúng một ca — kịch bản "corpus không có tin blockchain" — mà model trả lời *đúng* (bài AsyncAPI thật sự dùng Ethereum/IPFS làm kênh C2). Nhãn mới là cái sai; đã đổi câu hỏi sang chủ đề vắng thật (sa thải nhân sự) **trước khi** chốt baseline.
    - ⚠️ **Ranh giới với `chat-rank-stability` (RS)** — hai bộ đo khác nhau, đừng nhầm chạy cái nào: RS đo **Context Relevance** (recall của `_rank`, hàm thuần, **miễn phí**, chạy **trong `pytest` mặc định**); bộ đo này đo **hai cạnh còn lại của RAG Triad** trên câu trả lời model đẻ ra (**gọi model, tốn tiền**, nên **ngoài `pytest` mặc định** — phần `--live` nằm sau `CHAT_EVAL_LIVE=1`). Cùng dùng chung corpus fixture; RS chưa land tại thời điểm 27/07 nên `build_fixture_chat.py` được viết ở đây và RS tái dùng lại.
    - **Snapshot ≠ đo pipeline hiện tại**: chạy offline chấm lại câu trả lời **đông lạnh** — rẻ, tất định, hợp để đọc lại và gate trong review, nhưng KHÔNG bắt được hồi quy prompt/model. Chỉ `--live` mới bắt.
  - **Query Reformulator (viết lại câu nối tiếp) CHƯA làm** — hoãn vì **phụ thuộc `chat-streaming-sse` (⑤)**, mà ⑤ nay đã land (27/07/2026) nên **điều kiện tiên quyết đã mở**; quyết định bật hay không vẫn là một change riêng. Reformulator là *thêm* một lượt gọi model — lưu ý số đo của ⑤: streaming che được độ trễ **cảm nhận** bằng status, nhưng TTFT thật vẫn 8–37s, nên một lượt tiền‑xử‑lý cộng vào đó không hề miễn phí. Hiện recall câu nối tiếp mù được chữa bằng bản gộp‑từ‑khoá tất định (0 gọi model). Đừng tưởng nó đã tồn tại trong `chat_intent`/`chat_service`.
  - **MỘT luồng + WORKING SET, `history` KHÔNG còn cô lập theo scope** (change `chat-context-depth`, 28/07/2026 — **đảo ngược** `chat-context-isolation` 24/07). Client gửi `referenced_insight_ids` (tin người dùng đang thao tác: mở trang chi tiết, bấm citation) **tách khỏi** `question`; server rót chúng vào **Ô SÂU**.
    - **Vì sao đảo**: cô lập theo scope chặn được context poisoning, nhưng chính nó làm hai bài đọc riêng không bao giờ nằm chung một luồng ⇒ "so sánh hai cái này" **không thể** trả lời. Đo 28/07: câu so sánh hồi chỉ recall@5 = **0/4**, hai tin đúng ở hạng 8–141. Hỏng **theo cấu trúc** — `_question_terms("Hai cái này khác nhau chỗ nào?")` không chứa từ nội dung nào, nên **không mức tinh chỉnh `_rank` nào chữa được**. Poisoning cũ là *mâu thuẫn* history-vs-context; khi cả hai bài cùng trong context thì mâu thuẫn không tồn tại. Bất biến thay thế: **N tin được trích GẦN NHẤT trong history phải còn mặt trong ngữ cảnh lượt hiện tại** (xem `chat-history-pinning` — câu chữ gốc là "*mọi* tin", và nó **không thực thi được**).
  - **GHIM tin đã trích trong history vào index** (change `chat-history-pinning`, 29/07/2026). Bất biến trên **chỉ là lời hứa** cho tới change này: `history` chảy vào `_history_block` → prompt, **không chạm** `_rank`/`_question_terms`/embedding, còn working set thì chỉ lớn lên khi người dùng **chủ động** mở trang chi tiết hoặc **bấm** citation. Đo 29/07 (ma trận 6×6 chủ đề, top-3 của `_rank` làm proxy cho tin đã trích): **47/90 = 52%** cặp (tin đã bàn, chủ đề mới) **rơi khỏi top-60**, tệ nhất hạng **118/179** — model đọc được cái *tên* trong history mà không có dòng dữ liệu nào. Sau khi ghim: **52% → 0%**, prompt vẫn đúng 60 tin.
    - **Bất biến đã THU HẸP, không phải được thực thi nguyên văn.** History đầy nhắc tới ~25 tin; ghim quá **6** chỗ là recall@K tụt khỏi baseline. Chọn: giữ recall, thu hẹp lời hứa — và nói rõ ra thay vì để câu cũ đứng đó sai.
    - ⚠️ **Chọn tin ghim QUÉT THEO LỚP, không cạn từng lượt** (sửa 29/07/2026, sau khi land). Bản đầu duyệt ngược history và lấy cạn từng lượt; nhưng một lượt trả lời toàn cục trích tới **5 nguồn** trong khi chỉ có 3 chỗ ghim ⇒ **đúng một lượt chen giữa đủ để đẩy sạch mọi thứ trước nó ra ngoài**. Đo thật: bàn tin X ở lượt 1, hỏi câu khác chủ đề ở lượt 2, thì tới lượt 3 tập ghim là 3 nguồn của **riêng lượt 2**, X đứng thứ **6** và văng khỏi trần — tức cơ chế chỉ phủ được đúng lượt liền trước, không phải "3 tin gần nhất của cuộc hội thoại". Nay vòng 1 lấy nguồn **thứ nhất của mỗi lượt** (mới trước), vòng 2 lấy nguồn thứ hai, v.v. → X lên hạng **2**. Ca phổ biến nhất (hỏi tiếp ngay sau một lượt) **trùng khít** bản cũ vì chỉ có một lượt để quét. Cái cần nhớ là **3 CHỦ ĐỀ gần nhất**, không phải 3 dòng trích gần nhất. Khoá bằng `test_pin_ids_mot_luot_khong_doc_chiem_het_cho`.
    - **Ghim KHÔNG mang thân bài** — kiểm chứng trên corpus: 5 định danh chỉ-có-trong-thân-bài (`SquashFS`, `HMAC-SHA256`, `Firecracker`, `RabbitMQ`, `Jubair`) xuất hiện **0 lần** trong title/signal của mọi tin. Nên hỏi một chi tiết thân bài về tin *chỉ được ghim* thì dòng nén không trả lời được; muốn sâu thì tin phải vào **ô sâu** (người dùng bấm citation, hoặc xếp hạng tự kéo lên). ⚠️ Đừng đo việc này bằng "câu trả lời có chứa chuỗi X không": **history giữ lại câu trả lời các lượt trước**, mà những câu đó thường đã nêu chính định danh đang hỏi (đo: 3/3 ca), nên phép đo đó tính cả *nhớ lại từ transcript* thành *ghim có tác dụng*.
    - **Ghim nằm TRONG `CHAT_INDEX_TOP_K`** (đẩy đuôi bảng xếp hạng ra), cùng luật với ô sâu ⇒ ngân sách token **không phình**. Đo bằng RS harness ở K hiệu dụng: ghim 3 → recall@K **0,968** + recall@5 **0,900** (trùng baseline, biên **3 hạng**); 5 → biên 1; 6 → biên 0; **7 → 0,954 GÃY**. Vách ở **hạng 54**; hạng 21–53 rỗng; **recall@5 không đổi ở mọi mức K xuống tận 10** — ghim ở đuôi không chạm đầu bảng.
    - ⚠️ **`CHAT_HISTORY_PIN_SLOTS` (3) — đổi ⇒ BẮT BUỘC chạy lại RS harness.** Vách hạng 54 là **một điểm dữ liệu trên corpus 179 tin**, không phải hằng số hệ thống. `0` = tắt, index trùng khít bản chưa có cơ chế (đường rollback).
    - **Ghim vào INDEX, KHÔNG vào ô sâu**, và đặt ở **CUỐI** index. Ô sâu là chỗ của working set do người dùng chủ động chọn; tin trong history cần **có mặt** chứ chưa chắc cần **đọc kỹ**. Đặt cuối vì prompt dặn "tin ở đầu danh sách đáng chọn hơn", mà tin ghim theo định nghĩa **không** liên quan tới câu hỏi lượt này. Khử trùng theo `insight.id` với cả ô sâu lẫn index — cấp hai số `[n]` cho một tin là dựng lại bẫy của `chat-citation-integrity`.
    - **`TurnCitation` nay mang `insight_id`.** Docstring cũ nói cố ý không mang vì "bề mặt tấn công cho client tự khai định danh" — đọc **sai** ranh giới tin cậy thật: `referenced_insight_ids` đã nhận id từ client từ `chat-context-depth`. Bất biến thật là *client không đưa được **văn bản tuỳ ý** vào prompt*, và nó không đổi (id vẫn phải tra ra insight `published` thật, qua đúng `_load_refs`). Khớp ngược theo `title` bị loại: phép mờ, tra nhầm thì ghim **sai tin trong im lặng**.
    - ⚠️ **Nạp tin ghim chạy NỐI TIẾP, đừng "tối ưu" vào cụm `asyncio.gather` sẵn có.** `AsyncSession` không an toàn khi hai truy vấn chạy đồng thời; cụm đó chỉ sống được vì nhánh vector phải chờ `_embed_question` (~0,37s) xong mới chạm DB. Thêm một truy vấn khởi động ngay vào đó là đua thẳng với `list_for_chat` — hỏng ngẫu nhiên dưới tải, không tái hiện được. Giá phải trả chỉ là một truy vấn khoá chính (~vài ms) so với 85% TTFT nằm ở lượt gọi model.
    - ⚠️ **`chat_answer_harness --live` KHÔNG phủ được change này**: `chat_scenarios.jsonl` có **0/98 kịch bản mang `history`**, nên nó không bao giờ đi qua đường ghim. Nó chỉ chứng minh *không hồi quy trên đường cũ* (Faith 0,98 · CitPrec 1,00 · AnsRel 0,96). Lưới thật là bộ đo **hội thoại hai lượt** qua endpoint thật, đo hai mặt: hỏi chủ đề MỚI có bị tin ghim kéo đi không (**0/4** lạc đề), và hỏi QUAY LẠI tin đã bàn có trả lời được không (**2/2**, trước change không với tới được). Hiện là script rời ở scratchpad — **chưa có lưới thường trực nào canh đường ghim**.
    - **KHÔNG nén history** (bác bỏ hạng mục To-Be, có số): history đầy trần = 5 lượt hỏi–đáp = **1.713/45.228 ký tự = 3,8%** prompt, mà bỏ hẳn ~30% prompt đã đo là **không đổi TTFT**. Nén thu về ~2%, tốn **+1 lượt gọi model**, và **làm ca 52% ở trên TỆ HƠN** vì vứt bớt chi tiết của đúng phần đang thiếu chỗ dựa. ⚠️ `MAX_HISTORY_TURNS = 10` là 10 **tin nhắn** = **5 lượt hỏi–đáp**, không phải 10 lượt như bản To-Be viết.
    - **Ô SÂU lấp TẤT ĐỊNH, không heuristic** (`CHAT_DEEP_SLOTS`=3): refs trước, còn chỗ lấp bằng tin xếp hạng cao nhất. `build_context()` là **hàm thuần**. Hệ quả có chủ đích: câu toàn cục **không ghim gì** vẫn được 3 bài sâu ⇒ chữa luôn "từ chối sai câu hỏi chi tiết" (đo: toàn cục **1/5 → 5/5**, mode B vốn đã 5/5 — dữ liệu luôn có, chỉ là tầng toàn cục không với tới). `index_limit` (`CHAT_INDEX_TOP_K`) đếm **CẢ** ô sâu.
    - **Đo được**: câu so sánh tường minh Comparison Adequacy **1,25 → 2,00 / 2** (8/8). Con số quyết định (16GB vs 18GB VRAM) nằm ở `why_it_matters`/`so_what` — field mà `build_index_block` **không** đưa vào.
    - **Độ trễ đo trên SSE, client singleton (điều kiện production)**: TTFT **2,6–3,9s**, tổng 2,9–7,3s, status đầu ở **0,0s** và status thứ hai (mang tên tin đang đọc kỹ) ở **0,44s**. Câu so sánh dài hơn ~3,4s so với câu thường, nhưng phần đó nằm SAU token đầu ⇒ streaming che. ⚠️ Con số "8,4s" từng ghi ở đây là **sai điều kiện** — đo trên đường blocking VÀ tạo client mới mỗi câu.
      - **Ba hướng tối ưu đã ĐO và LOẠI**: (a) cắt ngắn câu trả lời — chỉ giảm phần sau token đầu, người dùng không cảm nhận; (b) bỏ raw content khỏi ô sâu — TTFT 3,3 → 3,2s (trong nhiễu) trong khi câu hỏi chi tiết **quay lại từ chối**; (c) hạ `CHAT_INDEX_TOP_K` — prefill không phải nút thắt, bỏ hẳn ~30% prompt không đổi TTFT. **85% TTFT là lượt gọi model**, và phần điều khiển được duy nhất trong đó là `CHAT_THINKING_BUDGET` — mà luật là "chỉ nâng, không hạ".
      - Van xả nếu buộc phải: `CHAT_DEEP_INCLUDE_CONTENT=false` (mất phần thắng câu chi tiết) → `CHAT_DEEP_SLOTS=2`. **Đừng hạ `CHAT_INDEX_TOP_K`**.
    - **Status thứ hai mang SỐ LIỆU THẬT** (`_reading_status`): tên 2 tin đang đọc kỹ + tổng tin khớp, phát ở ~0,44s. Đây là cải thiện DUY NHẤT còn rẻ — TTFT thật không cắt được, status mới là thứ chữa (bài học `chat-streaming-sse`). Mode B giữ `STATUS_COMPOSING` chung chung vì nó không đi qua `build_context`.
    - **Marker `[n]` trong history giải thành TIÊU ĐỀ**, không giữ số: bảng ánh xạ dựng lại mỗi lượt nên `[3]` lượt trước trỏ tin khác lượt này. Đây là bug **đã tồn tại** trước change. `ChatTurn` vì thế mang thêm `citations: [{n, title}]`; lượt thiếu citations → marker bị **bỏ** (số vô nghĩa tệ hơn không có gì).
    - **Đường `insight_id` cũ giữ NGUYÊN XI** (mode B + sentinel + expanded) cho client cũ, test, và 17 kịch bản `expanded` của `chat_answer_harness`. Có refs ⇒ `mode="focused"`, **1 lượt gọi**, không sentinel — context đã mang cả ô sâu lẫn index toàn cục nên không còn gì để mở rộng. Widget gửi `insight_id=null` khi có refs.
    - **Badge phạm vi hai chiều của `chat-scope-routing` KHÔNG còn** — thay bằng hàng chip working set (bỏ được từng mục). `ChatWidget.scope.test.tsx` → `ChatWidget.workingset.test.tsx`; `ChatWidget.drift.test.tsx` **viết lại** quanh bất biến mới; block "huỷ khi đổi scope" của streaming test bị đảo (một luồng ⇒ điều hướng **không** huỷ, huỷ mới là mất dữ liệu đã trả tiền sinh ra).
    - `build_fixture_chat` nay có **`--top-up`**: bản không cờ **ghi đè `chat_corpus.jsonl` bằng DB hiện tại**, nên thêm kịch bản mà chạy nó là vô tình đổi ảnh chụp corpus và mọi baseline mất tính so sánh được.
    - Nhóm RS **`comparison_anaphora` cố ý ĐỎ** (recall@5 = 0,00) — nó là **mốc đo** cho working set, không phải mục tiêu của `_rank`. Đừng "chữa" bằng cách sửa câu hỏi cho gần chữ trong tin.
- **Nhịp cron bản tin — hai cái bẫy**: KHÔNG dùng `IntervalTrigger(days=3)` (APScheduler dùng memory jobstore nên mỗi lần restart mốc kế tiếp tính lại từ lúc start ⇒ nhịp trôi dạt, restart nhiều có thể không bao giờ gửi) và KHÔNG dùng cron `day='*/3'` (là ngày-**trong-tháng**: 1,4,…,31 rồi nhảy mùng 1 = cách nhau 1 ngày). Dùng `day_of_week` như hiện tại.
- **Chọn tin gửi: xếp hạng, KHÔNG lọc ngưỡng**: đo thật trên cửa sổ 108h, vai trò `Security` có 26 insight `urgency=high` còn `Data Scientist` có **0** (dù khớp 29 tin) — lọc theo ngưỡng vừa làm ngập người này vừa bỏ đói người kia. `score_for_role()` xếp theo urgency vai trò → impact_label → có `practical_indicators` cụ thể → actionability_score → Strategic → trust_score → mới hơn, rồi lấy top-N cứng. Cột `insights.urgency` **không dùng ở đây** (nó suy tất định từ impact_label và trên dữ liệu thật không có giá trị `high` nào).
- **`delivery_log` chỉ ghi tin ĐÃ GỬI, nên unique constraint KHÔNG chặn được lần chạy thừa**: luật cũ của digest ("ghi log cả phần vượt cap") sinh ra khi digest gửi mọi tin khớp, cap 15 chỉ giới hạn hiển thị. Với trần 3 tin/email, giữ luật đó sẽ chôn vĩnh viễn hàng chục tin chưa ai đọc — nên nay chỉ log tin đã gửi, tin bị loại vì trần còn quyền cạnh tranh ở kỳ kế tiếp. **Hệ quả đo được 21/07**: chạy `run_delivery --send` hai lần liên tiếp thì lần hai gửi thêm 3 tin nữa (lô xếp hạng kế tiếp, toàn tin khác nên lọt qua constraint), `delivery_log` 9 → 18 dòng, 0 tin trùng. Vì vậy phải có **chốt chặn chu kỳ** `DeliveryLogRepository.sent_within()` + `DELIVERY_MIN_GAP_HOURS` (48) — đừng gỡ nó vì tưởng unique constraint đã đủ. `run_delivery --force` bỏ qua chốt này khi test.
- **Email vào Spam khi gửi từ Gmail cá nhân + link `localhost`** (đo thật 21/07/2026): không phải lỗi template, đừng chỉnh CSS/câu chữ để chữa. Nguyên nhân theo sức nặng: (1) người gửi `@gmail.com` cá nhân không có domain tích luỹ danh tiếng gửi hàng loạt; (2) mọi link trỏ `localhost` — link không phân giải được là tín hiệu spam mạnh, cần `DASHBOARD_BASE_URL`/`PUBLIC_API_BASE_URL` công khai thật; (3) header `List-Unsubscribe` khai báo thư hàng loạt (đúng chuẩn, PHẢI giữ) cộng hai thứ trên thành hồ sơ đáng ngờ. Cách chữa thật: gửi từ Workspace domain công ty (DKIM/DMARC gắn domain) → URL công khai → người nhận đánh dấu "Không phải thư rác" + thêm vào danh bạ.
- **Playwright / CloakBrowser crawl** (`source_type: playwright`): `PlaywrightConnector` prefers CloakBrowser via CDP (`CLOAK_CDP_URL`, default `http://cloak:9222`; set empty to force local Chromium). LinkedIn sources need a valid login session file (`config.cookie_file` → `/secrets/states/linkedin_state.json`) created via `playwright codegen --save-storage=...` — see `docs/session_bootstrap.md`. X/Twitter sources were removed on 2026-07-20 (tweets too short to yield insights, duplicated official RSS) — `LOGIN_WALL_URL_MARKERS`/`LOGIN_URLS` cover LinkedIn only. Sessions self-renew (sliding refresh) after successful runs, so the `secrets/states` mount is **rw** (not `:ro`). Fingerprint is URL+title, so N different URLs returning the same shell page would each be stored — `PlaywrightConnector._dedup_by_content` drops in-batch content duplicates to prevent that.

## Documentation Map

For deeper context, see:
- `docs/specs/01_project_overview_and_brd.md` — Business goals, KPIs, target users
- `docs/specs/04_solution_architecture.md` — 7-layer architecture vision
- `docs/specs/05_data_model_erd_and_api_spec.md` — Full data model and API spec
- `docs/specs/07_source_strategy_and_source_catalog_v_1.md` — RSS source catalog and trust rationale
- `docs/system_overview.md` — Operational guide in Vietnamese
- `openspec/specs/` — Capability-level BDD specs (current implemented state)
