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

# Delivery (Telegram) — run alert cycle / digest manually
docker-compose exec backend python -m app.scripts.run_delivery --alert
docker-compose exec backend python -m app.scripts.run_delivery --digest
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
- **`channels/`** — `ChannelAdapter` interface + `DeliveryMessage` (channel-neutral) + `TelegramAdapter`/`TelegramAPI` (HTML parse mode, escape động, split >4096 chars). Registry pattern như connectors.
- **`bot/`** — Telegram transport: `worker.py` (long-polling `getUpdates`, backoff, heartbeat), `router.py` (route lệnh/callback/text; `register_chat_handler()` là hook cho chatbot-qa qua `app.state.bot_router`), `handlers.py` (subscription flow `/start` `/subscribe` `/unsubscribe` `/status` — inline keyboard đa chọn 9 `ALLOWED_ROLES`)
- **`services/delivery_engine.py`** — M7 Delivery: alert critical (job 5 phút, lookback 24h, trần alert/giờ → gom tổng hợp) + digest ngày (giờ VN, lookback 48h, cap 15 hiển thị nhưng log hết); chống trùng qua `delivery_log` unique (insight_id, chat_id, kind); thuần template, KHÔNG gọi Gemini
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

Key models: `Source` (RSS feeds with trust_tier, **`region`** ∈ `global`/`china`/`vietnam`, **`target_roles`** VARCHAR[]) → `RawDocument` (fetched content, processing_status) → `Insight` (analyzed output). Delivery: `Subscriber` (chat_id BigInteger PK, roles[] từ `ALLOWED_ROLES`, active) + `DeliveryLog` (unique insight_id+chat_id+kind — idempotent).

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
- `recommendations` (JSONB) — `{ role: { action_type, note } }`, keys ⊆ `affected_roles`
- `risks` (TEXT[]) — danh sách rủi ro nếu adopt; có thể `[]`

**Rule-based (computed in `AnalyzerService` / `DeduplicationEngine`):**
- `momentum` (`new` | `rising` | `mature`) — derive từ cluster size + age (`compute_momentum` in dedup_engine)
- `urgency` (`critical` | `high` | `medium` | `low`) — `_compute_urgency(impact_label, published_at)`
- `vietnam_relevance` (`high` | `medium` | `low`) — `_compute_vietnam_relevance(source, topics)`

**Closed set `ALLOWED_ACTION_TYPES`** (in `app/ai/prompts.py`): `watch`, `read`, `test`, `PoC`, `roadmap`.

Backwards compatible: insights cũ chưa có 7 fields trả `null`; UI hide gracefully (không render placeholder).

Regenerate insights cũ với prompt v2: `docker-compose exec backend python -m app.scripts.regenerate_insights --limit 50`.

## Vietnamese Taxonomy (Closed Sets)

Defined in `backend/app/ai/prompts.py`. Adding or renaming values here requires updating the Gemini prompt **and** any frontend labels that map to them.

**Topics (`ALLOWED_TOPICS`):**
Trí tuệ nhân tạo, Công nghệ, Dữ liệu, Quy trình phần mềm, An ninh mạng, Pháp lý/Tuân thủ, Nội dung/Marketing, Dịch vụ/Nền tảng, Thị trường/Đối thủ, Quản trị nội bộ

**Event Types (`ALLOWED_EVENT_TYPES`):**
Phát hành mới, Thay đổi chính sách, Cập nhật quy định, Cảnh báo bảo mật, Ngừng hỗ trợ, Tín hiệu xu hướng, Thảo luận cộng đồng, Cập nhật nghiên cứu, Sự cố vận hành

**Nature (`ALLOWED_NATURES`):**
Rủi ro, Cơ hội, Tuân thủ, Thông tin chung, Theo dõi

**Affected Roles (`ALLOWED_ROLES`):**
Executive, Engineering, Data/AI, Product, Content/Marketing, Legal/Compliance, HR/L&D, DevOps, Infrastructure, Security, BA/QA, Designer/UX, Toàn công ty

5 vai trò technical (DevOps/Infrastructure/Security/BA/QA/Designer/UX) thêm vào 2026-05-09 — Gemini chọn role specific nhất; Engineering là fallback nếu không match. Chi tiết phân biệt: DevOps (CI/CD, deployment), Infrastructure (cloud, network), Security (AppSec, CVE, compliance kỹ thuật), BA/QA (requirements, test automation), Designer/UX (design system).

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
- **Delivery + --reload**: `DELIVERY_ENABLED=true` cần `TELEGRAM_BOT_TOKEN`; không chạy kèm `uvicorn --reload` (long-polling trùng sau reload → Telegram trả 409 Conflict). Env liên quan: `DELIVERY_DIGEST_HOUR` (giờ **VN**, không phải UTC), `DELIVERY_ALERT_INTERVAL_MINUTES`, `DELIVERY_MAX_ALERTS_PER_HOUR`, `DELIVERY_ALERT_LOOKBACK_HOURS`/`DELIVERY_DIGEST_LOOKBACK_HOURS`, `DASHBOARD_BASE_URL`. Subscription roles dùng 9 `ALLOWED_ROLES` trong `prompts.py`, KHÔNG phải 13 `target_roles` của Source.
- **Playwright / CloakBrowser crawl** (`source_type: playwright`): `PlaywrightConnector` prefers CloakBrowser via CDP (`CLOAK_CDP_URL`, default `http://cloak:9222`; set empty to force local Chromium). X/LinkedIn sources need a valid login session file (`config.cookie_file` → `/secrets/states/*.json`) created via `playwright codegen --save-storage=...` — see `docs/session_bootstrap.md`. Sessions self-renew (sliding refresh) after successful runs, so the `secrets/states` mount is **rw** (not `:ro`). Fingerprint is URL+title, so N different URLs returning the same shell page would each be stored — `PlaywrightConnector._dedup_by_content` drops in-batch content duplicates to prevent that.

## Documentation Map

For deeper context, see:
- `docs/specs/01_project_overview_and_brd.md` — Business goals, KPIs, target users
- `docs/specs/04_solution_architecture.md` — 7-layer architecture vision
- `docs/specs/05_data_model_erd_and_api_spec.md` — Full data model and API spec
- `docs/specs/07_source_strategy_and_source_catalog_v_1.md` — RSS source catalog and trust rationale
- `docs/system_overview.md` — Operational guide in Vietnamese
- `openspec/specs/` — Capability-level BDD specs (current implemented state)
