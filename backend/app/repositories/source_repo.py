"""Repository for Source DB operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
