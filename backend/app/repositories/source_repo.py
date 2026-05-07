"""Repository for Source DB operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.models.source import Source


class SourceRepository:
    """Data access layer for sources table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_sources(self) -> list[Source]:
        """Return all sources with status='active'."""
        result = await self.session.execute(
            select(Source).where(Source.status == "active")
        )
        return list(result.scalars().all())

    async def get_by_id(self, source_id: uuid.UUID) -> Source | None:
        """Return a source by its UUID."""
        return await self.session.get(Source, source_id)

    async def list_with_insight_counts(self) -> list[dict]:
        """Return sources with published insight counts."""
        result = await self.session.execute(
            select(
                Source.id,
                Source.name,
                Source.source_type,
                Source.status,
                func.count(Insight.id).label("insight_count"),
            )
            .outerjoin(RawDocument, RawDocument.source_id == Source.id)
            .outerjoin(
                Insight,
                (Insight.raw_document_id == RawDocument.id)
                & (Insight.status == "published"),
            )
            .group_by(Source.id)
            .order_by(Source.name.asc())
        )
        return [dict(row._mapping) for row in result]
