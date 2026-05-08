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

- **`connectors/`** — RSS fetching via feedparser (`RSSConnector`)
- **`services/`** — Business logic: `IngestionService` (fetch → normalize → dedup → store), `AnalyzerService` (pending docs → Gemini → Insight)
- **`ai/`** — `GeminiClient` wraps google-genai SDK; prompt templates define allowed topics/event_types/roles in Vietnamese
- **`repositories/`** — Data access layer (InsightRepository, RawDocumentRepository, SourceRepository)
- **`models/`** — SQLAlchemy async ORM (UUIDs, PostgreSQL arrays)
- **`schemas/`** — Pydantic v2 request/response validation
- **`routes/`** — FastAPI endpoints under `/api/v1/`
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

PostgreSQL 16. All PKs are UUIDs. Deduplication uses SHA256 fingerprints on normalized content. Migrations are in `backend/alembic/`.

Key models: `Source` (RSS feeds with trust_tier) → `RawDocument` (fetched content, processing_status) → `Insight` (analyzed output).

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

## Vietnamese Taxonomy (Closed Sets)

Defined in `backend/app/ai/prompts.py`. Adding or renaming values here requires updating the Gemini prompt **and** any frontend labels that map to them.

**Topics (`ALLOWED_TOPICS`):**
Trí tuệ nhân tạo, Công nghệ, Dữ liệu, Quy trình phần mềm, An ninh mạng, Pháp lý/Tuân thủ, Nội dung/Marketing, Dịch vụ/Nền tảng, Thị trường/Đối thủ, Quản trị nội bộ

**Event Types (`ALLOWED_EVENT_TYPES`):**
Phát hành mới, Thay đổi chính sách, Cập nhật quy định, Cảnh báo bảo mật, Ngừng hỗ trợ, Tín hiệu xu hướng, Thảo luận cộng đồng, Cập nhật nghiên cứu, Sự cố vận hành

**Nature (`ALLOWED_NATURES`):**
Rủi ro, Cơ hội, Tuân thủ, Thông tin chung, Theo dõi

**Affected Roles (`ALLOWED_ROLES`):**
Executive, Engineering, Data/AI, Product, Content/Marketing, Legal/Compliance, HR/L&D, Toàn công ty

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
- **AWS What's New source name**: The source name contains a Unicode right single quotation mark (`'`, U+2019) instead of a regular apostrophe. Exact-match DB lookups against this source name must use the correct character.
- **Content limit in prompt**: Gemini prompt truncates content to 6000 chars (`prompts.py:87`). Longer articles are silently cut — this affects arXiv and long blog posts.
- **Confidence threshold mismatch**: `openspec/specs/ai-analysis/spec.md` says confidence < 0.5 → `needs_review`, but actual code uses 0.3 as the discard threshold with no `needs_review` state. The spec is aspirational; code is authoritative.

## Documentation Map

For deeper context, see:
- `docs/specs/01_project_overview_and_brd.md` — Business goals, KPIs, target users
- `docs/specs/04_solution_architecture.md` — 7-layer architecture vision
- `docs/specs/05_data_model_erd_and_api_spec.md` — Full data model and API spec
- `docs/specs/07_source_strategy_and_source_catalog_v_1.md` — RSS source catalog and trust rationale
- `docs/system_overview.md` — Operational guide in Vietnamese
- `openspec/specs/` — Capability-level BDD specs (current implemented state)
