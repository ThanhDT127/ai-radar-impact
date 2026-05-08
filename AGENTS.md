<claude-mem-context>
</claude-mem-context>

# Agent Instructions — AI Radar Impact

This file provides guidance to Claude Code subagents spawned within this project. Read CLAUDE.md first for full project context, architecture, taxonomy, and known gotchas. This file adds agent-specific rules on top.

---

## Project in One Paragraph

AI Radar Impact ingests RSS feeds from 15 tech/AI sources, runs each article through Gemini 2.5 Flash (Vertex AI) for Vietnamese classification and summarization, then surfaces the results as insight cards on a React dashboard. Stack: FastAPI + PostgreSQL (async SQLAlchemy) + React 19 + Vite. All user-facing content and AI output is in Vietnamese.

---

## Non-Negotiable Rules

- **Never drop or truncate database tables.** Use `alembic downgrade` if a migration needs reverting.
- **Never run sync SQLAlchemy calls.** All DB operations use `async with session` — a sync call will deadlock silently.
- **Never modify `ALLOWED_TOPICS`, `ALLOWED_EVENT_TYPES`, `ALLOWED_NATURES`, or `ALLOWED_ROLES` in `prompts.py` without also updating the frontend label mappings.** These are closed sets; adding a value breaks existing filter UI.
- **Never commit `.env` or `secrets/sa-key.json`.** Both are gitignored for a reason.
- **Always run migrations after schema changes.** `docker-compose exec backend alembic upgrade head`.

---

## Task-Specific Guidance

### Exploring / Reading Code

- Entry points by concern:
  - Data pipeline: `backend/app/services/ingestion.py`, `backend/app/services/analyzer.py`
  - AI prompt: `backend/app/ai/prompts.py`, `backend/app/ai/gemini_client.py`
  - API routes: `backend/app/routes/` — note router registration order in `main.py` (stats before /{id})
  - Frontend state: `frontend/src/pages/InsightList.tsx`, `frontend/src/api/insights.ts`
- Read `openspec/specs/` for BDD-style specs of each capability before modifying behavior.

### Implementing Backend Features

- All new routes go under `/api/v1/`. Register in `backend/app/main.py`.
- Repository pattern is mandatory — business logic stays in `services/`, DB queries stay in `repositories/`.
- New DB columns require an Alembic migration. Generate with:
  `docker-compose exec backend alembic revision --autogenerate -m "description"`
- Pydantic v2 schemas in `schemas/` — use `model_validator` not `validator`.
- Content sent to Gemini is capped at 6000 chars in `build_prompt()`. Keep this limit in mind for chunking decisions.

### Implementing Frontend Features

- API calls go in `frontend/src/api/` — no direct axios calls from components or pages.
- All server state via TanStack Query. Local UI state (filters, pagination, active tab) via `useState`.
- CSS Modules only — no inline styles, no global class mutations.
- Vietnamese text is the default language for all labels, badges, and messages.

### Modifying the AI Pipeline

- The Gemini prompt is in `backend/app/ai/prompts.py`. Any structural change to the JSON schema the model must return also requires updating the `AnalysisResult` dataclass in `gemini_client.py` and the `create()` call in `analyzer.py`.
- Confidence threshold for publishing is `MIN_CONFIDENCE = 0.3` in `analyzer.py`. The OpenSpec spec says 0.5 — trust the code, not the spec.
- Trust score and impact label are **rule-based**, not AI-generated. Mappings live in `TRUST_SCORE_MAP` and `IMPACT_LABEL_MAP` in `analyzer.py`.
- After changing prompts, run a test on a small batch: `docker-compose exec backend python -m app.scripts.run_analysis`

### Running / Debugging the Pipeline

```bash
# Check what's pending vs analyzed vs failed
docker-compose exec backend python -c "
import asyncio
from app.database import AsyncSessionLocal
from app.repositories.raw_document_repo import RawDocumentRepository
async def check():
    async with AsyncSessionLocal() as s:
        r = RawDocumentRepository(s)
        print(await r.get_status_counts())
asyncio.run(check())
"

# Re-queue failed documents for retry
docker-compose exec backend python -m app.scripts.reset_failed

# Run analysis on up to N pending docs
docker-compose exec backend python -m app.scripts.run_analysis
```

### Verifying Against OpenSpec

Before reporting a task complete, check the relevant spec in `openspec/specs/<capability>/spec.md`. Each spec uses BDD scenario format (`WHEN … THEN …`). Verify each scenario is satisfied by the implementation, not just that the code compiles.

---

## What NOT to Do

- Do not add `print()` debug statements to production code — use `logger = logging.getLogger(__name__)`.
- Do not create new scripts in `backend/app/scripts/` for one-off investigation — run inline via `docker-compose exec backend python -c "..."`.
- Do not add comments that explain what the code does — only add comments for non-obvious WHY (constraints, workarounds, invariants).
- Do not introduce new dependencies without checking if an existing library already in `requirements.txt` covers the need.
