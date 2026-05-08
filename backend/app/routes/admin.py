"""Admin API routes — trigger ingestion/analysis, manage sources."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.middleware.admin_auth import verify_admin_key
from app.repositories.source_repo import SourceRepository
from app.schemas.source import SourceCreate, SourceListItem
from app.services.analyzer import AnalyzerService, _get_daily_count
from app.services.ingestion import IngestionService

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin_key)],
)


@router.post("/ingest")
async def trigger_ingest(
    source_id: Annotated[uuid.UUID | None, Query()] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Trigger ingestion for all active sources or a single source by ID."""
    service = IngestionService(session)
    summary = await service.run(source_id=source_id)
    return {
        "status": "completed",
        "summary": {
            "new": summary.new,
            "skipped": summary.skipped,
            "errors": summary.errors,
            "insights_created": summary.insights_created,
        },
    }


@router.post("/analyze")
async def trigger_analyze(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Trigger AI analysis for all pending raw documents."""
    daily_used = _get_daily_count()
    if daily_used >= settings.max_daily_analysis:
        raise HTTPException(
            status_code=429,
            detail=f"Daily analysis limit reached ({settings.max_daily_analysis})",
        )

    service = AnalyzerService(session)
    counts = await service.run_pending(limit=50)
    return {"status": "completed", "summary": counts}


@router.get("/sources", response_model=list[SourceListItem])
async def list_sources(
    session: AsyncSession = Depends(get_session),
) -> list[SourceListItem]:
    """List all sources with published insight counts."""
    repo = SourceRepository(session)
    items = await repo.list_with_insight_counts()
    return [SourceListItem.model_validate(item) for item in items]


@router.post("/sources", status_code=201)
async def add_source(
    body: SourceCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Add a new source."""
    repo = SourceRepository(session)
    source = await repo.create(
        name=body.name,
        source_type=body.source_type,
        feed_url=body.feed_url,
        trust_tier=body.trust_tier,
        topics=body.topics,
        status=body.status,
        config=body.config,
    )
    await session.commit()
    return {"id": str(source.id), "name": source.name, "status": source.status}
