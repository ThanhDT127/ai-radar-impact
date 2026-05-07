"""Source API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.source_repo import SourceRepository
from app.schemas.source import SourceListItem

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("", response_model=list[SourceListItem])
async def list_sources(
    session: AsyncSession = Depends(get_session),
) -> list[SourceListItem]:
    """Return all sources with published insight counts."""
    repo = SourceRepository(session)
    items = await repo.list_with_insight_counts()
    return [SourceListItem.model_validate(item) for item in items]
