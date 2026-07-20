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

    async def create(
        self,
        *,
        name: str,
        source_type: str,
        feed_url: str | None,
        trust_tier: str,
        topics: list[str],
        status: str,
        config: dict,
        region: str = "global",
        target_roles: list[str] | None = None,
    ) -> Source:
        """Insert a new source and return it."""
        source = Source(
            name=name,
            source_type=source_type,
            feed_url=feed_url,
            trust_tier=trust_tier,
            topics=topics,
            status=status,
            config=config,
            region=region,
            target_roles=target_roles or [],
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def list_with_insight_counts(self) -> list[dict]:
        """Return sources with published insight counts."""
        result = await self.session.execute(
            select(
                Source.id,
                Source.name,
                Source.source_type,
                Source.status,
                Source.region,
                Source.target_roles,
                func.count(Insight.id).label("insight_count"),
            )
            .outerjoin(RawDocument, RawDocument.source_id == Source.id)
            # `is_primary` nằm trong điều kiện ON của outer join, KHÔNG phải where:
            # đưa vào where sẽ làm biến mất mọi nguồn không có insight primary, hỏng
            # nhóm "chưa có insight" trên UI. Ở ON thì hàng vẫn còn, count về 0.
            .outerjoin(
                Insight,
                (Insight.raw_document_id == RawDocument.id)
                & (Insight.status == "published")
                & (Insight.is_primary == True),  # noqa: E712
            )
            .group_by(Source.id)
            .order_by(Source.name.asc())
        )
        return [dict(row._mapping) for row in result]
