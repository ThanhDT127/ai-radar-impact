"""Insight stats API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.insight_repo import InsightRepository
from app.schemas.source import InsightStats

router = APIRouter(prefix="/api/v1/insights/stats", tags=["insights"])


@router.get("", response_model=InsightStats)
async def get_insight_stats(
    session: AsyncSession = Depends(get_session),
) -> InsightStats:
    """Return summary KPI stats for the dashboard."""
    repo = InsightRepository(session)
    stats = await repo.get_stats()
    return InsightStats.model_validate(stats)
