"""Repository for Insight DB operations."""

import uuid
from datetime import datetime

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import Insight

# Impact label ordering for sort (Vietnamese)
_IMPACT_ORDER = case(
    (Insight.impact_label == "Nghiêm trọng", 1),
    (Insight.impact_label == "Cao", 2),
    (Insight.impact_label == "Trung bình", 3),
    (Insight.impact_label == "Thấp", 4),
    (Insight.impact_label == "Theo dõi", 5),
    else_=6,
)


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
        affected_roles: list[str] | None = None,
        published_at: datetime | None = None,
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
            affected_roles=affected_roles or [],
            published_at=published_at,
            status="published",
        )
        self.session.add(insight)
        await self.session.flush()
        return insight

    async def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        role: str | None = None,
        source_id: uuid.UUID | None = None,
        sort_by: str = "created_at",
    ) -> tuple[list[Insight], int]:
        """Return paginated insights with optional role/source filters and sort.

        sort_by options: "created_at" | "published_at" | "impact_label"
        Returns (items, total).
        """
        offset = (page - 1) * size

        base_query = select(Insight).where(Insight.status == "published")

        # Filter by role (match any in affected_roles array)
        if role:
            base_query = base_query.where(Insight.affected_roles.any(role))

        # Filter by source via join on raw_document
        if source_id:
            from app.models.raw_document import RawDocument  # noqa: PLC0415
            base_query = base_query.join(
                RawDocument, Insight.raw_document_id == RawDocument.id
            ).where(RawDocument.source_id == source_id)

        # Sort
        if sort_by == "published_at":
            order = Insight.published_at.desc().nulls_last()
        elif sort_by == "impact_label":
            order = _IMPACT_ORDER
        else:
            order = Insight.created_at.desc()

        # Count total matching rows
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Fetch page
        result = await self.session.execute(
            base_query.order_by(order).offset(offset).limit(size)
        )
        items = list(result.scalars().all())
        return items, total

    async def get_by_id(self, insight_id: uuid.UUID) -> Insight | None:
        """Return a single insight by UUID, or None."""
        return await self.session.get(Insight, insight_id)
