"""Repository for Insight DB operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import Insight


class InsightRepository:
    """Data access layer for insights table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        raw_document_id: uuid.UUID,
        title: str,
        summary_short: str | None,
        summary_medium: str | None,
        topics: list[str],
        event_type: str | None,
        nature: str | None,
        trust_score: float,
        impact_label: str | None,
        source_url: str,
        confidence: float,
        ai_raw_response: dict,
    ) -> Insight:
        """Insert a new insight and return it."""
        insight = Insight(
            raw_document_id=raw_document_id,
            title=title,
            summary_short=summary_short,
            summary_medium=summary_medium,
            topics=topics,
            event_type=event_type,
            nature=nature,
            trust_score=trust_score,
            impact_label=impact_label,
            source_url=source_url,
            confidence=confidence,
            ai_raw_response=ai_raw_response,
            status="published",
        )
        self.session.add(insight)
        await self.session.flush()
        return insight

    async def list_paginated(
        self, page: int = 1, size: int = 20
    ) -> tuple[list[Insight], int]:
        """Return paginated insights sorted by created_at DESC.

        Returns (items, total).
        """
        offset = (page - 1) * size

        total_result = await self.session.execute(
            select(func.count()).select_from(Insight).where(Insight.status == "published")
        )
        total = total_result.scalar_one()

        result = await self.session.execute(
            select(Insight)
            .where(Insight.status == "published")
            .order_by(Insight.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        items = list(result.scalars().all())
        return items, total

    async def get_by_id(self, insight_id: uuid.UUID) -> Insight | None:
        """Return a single insight by UUID, or None."""
        return await self.session.get(Insight, insight_id)
