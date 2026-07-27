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

PostgreSQL 16. All PKs are UUIDs. Deduplication uses SHA256 fingerprints computed from **`source_url` + `title`** (see `normalizer.make_fingerprint`), not from content body. Migrations are in `backend/alembic/`.

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
    - Env: `MAX_DAILY_CHAT_CALLS` (200), `CHAT_INDEX_TOP_K` (**60**; 0 = không cắt), `CHAT_WINDOW_DAYS` (0 = cả corpus), `INTENT_CLASSIFIER_ENABLED`, `INTENT_CLASSIFIER_MODEL_ID`.
  - **Citation do server cấp phát**: prompt KHÔNG chứa UUID, model chỉ trả text thuần có marker `[n]`, server tra bảng `n → insight_id`. Chống bịa bằng **cấu trúc**, không phải hậu kiểm — đừng "tiện tay" thêm id vào index.
  - **`n` là SỐ INDEX, không phải vị trí trong mảng `citations`** (change `chat-citation-integrity`, 27/07/2026). Backend đánh số theo index (1..60); `citations[]` chỉ nén những tin được trích (1..k, k≤5). Widget cũ tra `citations[n-1]` — trộn hai hệ quy chiếu, và **chỉ đúng khi model trích liền mạch từ [1]**, điều nó thường làm chỉ vì prompt dặn "tin ở đầu danh sách đáng chọn hơn". Tức là bất biến dựa vào **thói quen của model**, và nó vỡ ngay khi model bỏ qua một tin ở giữa (`[1][2][4]`). Nay `Citation` mang trường **`n`** tường minh; frontend giải bằng `citations.find(c => c.n === n)`. **Đừng "tối ưu" về phép tính chỉ số.**
    - Marker trong answer **giữ nguyên số**, server KHÔNG đánh số lại (đánh lại là *viết lại* output của model, và đá nhau khi câu trả lời tự nhắc "tin số 3 ở trên"). Danh sách nguồn dưới bong bóng vì thế hiện `[3][7][12]` — **khớp marker inline**, không phải `[1][2][3]`.
    - Đây là lỗi **sống ở khe giữa hai tầng**: `test_resolve_citations_maps_markers_in_order` khẳng định `[2]→B, [1]→A` và **xanh** ở backend, trong khi chính ca đó làm widget trỏ sai cả hai. Test một bên ranh giới không bảo vệ được ranh giới — lưới thật là `frontend/src/components/__tests__/chatAnswer.boundary.test.ts` (6 dãy marker, kèm một test đối chứng chứng minh cách cũ sai 5/6).
    - Marker không liền mạch từ 1 được log mức **DEBUG** ở `resolve_citations` — tín hiệu sớm cho việc xếp hạng đặt tin lệch vào top. Quan sát, không phải lỗi.
  - **Chat KHÔNG dùng `response_mime_type`/`response_schema`** (bài học `gemini-structured-output`: output dài + schema = runaway → JSON vỡ).
  - **⚠️ Đơn vị budget khác nhau**: `MAX_DAILY_ANALYSIS` đếm *tài liệu* (1 tài liệu = 2 lượt gọi model), `MAX_DAILY_CHAT_CALLS` đếm *lượt gọi*. Counter chat là `SUM(chat_logs.model_calls)` theo ngày UTC — bảng log cũng chính là counter.
  - **Thinking tokens chi phối chi phí/độ trễ**: đo thật 121→3.791 token/câu, bị tính tiền như output ($2,50/1M) → $0,006-0,016/câu và 5-22,6s (không phải $0,007 và 3-6s như ước tính ban đầu). `thinking_budget` cần `google-genai` 1.x; bản pin 0.8.0 chỉ có `ThinkingConfig(include_thoughts)`.
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
  - **Query Reformulator (viết lại câu nối tiếp) CHƯA làm** — cố ý hoãn, **phụ thuộc `chat-streaming-sse` (⑤)**: reformulator là *thêm* một lượt gọi model, chỉ đáng khi streaming đã che độ trễ cảm nhận. Trước đó recall câu nối tiếp mù được chữa bằng bản gộp‑từ‑khoá tất định (0 gọi model). Đừng tưởng nó đã tồn tại trong `chat_intent`/`chat_service`.
  - **`history` widget gửi lên PHẢI cô lập theo scope** (change `chat-context-isolation`, 24/07/2026): mỗi scope — một `insight_id` cụ thể, hoặc toàn cục (`"__global__"`) — có luồng hội thoại riêng trong `ChatWidget`. `send()` dựng `history` từ **luồng của scope hiện tại**, KHÔNG từ một mảng `messages` gộp cả phiên. Gộp xuyên scope = context poisoning (Nguy hiểm #3 báo cáo To-Be): đổi bài A→B rồi hỏi câu nối tiếp mập mờ ("nó", "rủi ro thì sao") thì server đọc bài B nhưng history nói về A → model resolve sai. Chip đã theo route từ trước, nhưng history thì **không** — sửa chip mà quên history là sửa nửa vời. ⚠️ **Context chip nói ở đây đã bị `chat-scope-routing` (25/07) thay bằng badge phạm vi hai chiều** — bất biến "history theo scope" giữ nguyên, chỉ đổi control. Đây là **bug chỉ sống ở state frontend, không lộ qua backend test**; đã có test `frontend/src/components/__tests__/ChatWidget.drift.test.tsx` (test frontend **đầu tiên** của repo, runner `vitest` — `npm test` trong `frontend/`) khoá bất biến "history theo scope" qua 3 ca A→B→A / bỏ chip / rời detail. **Đừng "gộp cho tiện"** — test sẽ đỏ.
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
