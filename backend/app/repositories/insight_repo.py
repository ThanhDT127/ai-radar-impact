"""Repository for Insight DB operations."""

import uuid
from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.models.source import Source

_IMPACT_ORDER = case(
    (Insight.impact_label.in_(["Nghiêm trọng", "Critical"]), 1),
    (Insight.impact_label.in_(["Cao", "High"]), 2),
    (Insight.impact_label.in_(["Trung bình", "Medium"]), 3),
    (Insight.impact_label.in_(["Thấp", "Low"]), 4),
    (Insight.impact_label.in_(["Theo dõi", "Watch"]), 5),
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
        roles: list[str] | None = None,
        source_ids: list[uuid.UUID] | None = None,
        sort_by: str = "created_at",
    ) -> tuple[list[dict], int]:
        """Return paginated insights with optional role/source filters and sort."""
        offset = (page - 1) * size

        base_query = (
            select(Insight)
            .join(RawDocument, Insight.raw_document_id == RawDocument.id)
            .join(Source, RawDocument.source_id == Source.id)
            .where(Insight.status == "published")
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
        )

        if roles:
            base_query = base_query.where(
                or_(*(Insight.affected_roles.any(role) for role in roles))
            )

        if source_ids:
            base_query = base_query.where(RawDocument.source_id.in_(source_ids))

        if sort_by == "published_at":
            order = Insight.published_at.desc().nulls_last()
        elif sort_by == "impact_label":
            order = _IMPACT_ORDER.asc()
        elif sort_by == "trust_score":
            order = Insight.trust_score.desc().nulls_last()
        else:
            order = Insight.created_at.desc()

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            base_query.order_by(order).offset(offset).limit(size)
        )
        items = [self._serialize_insight(item) for item in result.scalars().unique().all()]
        return items, total

    async def get_by_id(self, insight_id: uuid.UUID) -> dict | None:
        """Return a single insight by UUID, or None."""
        result = await self.session.execute(
            select(Insight)
            .where(Insight.id == insight_id)
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
        )
        insight = result.scalar_one_or_none()
        if insight is None:
            return None
        return self._serialize_insight(insight)

    async def get_stats(self) -> dict[str, int]:
        """Return dashboard KPI stats."""
        totals = await self.session.execute(
            select(
                func.count(Insight.id).label("total"),
                func.count(Insight.id)
                .filter(
                    Insight.impact_label.in_(
                        ["Nghiêm trọng", "Cao", "Critical", "High"]
                    )
                )
                .label("critical_high"),
                func.count(Insight.id)
                .filter(Insight.nature.in_(["Cơ hội", "Opportunity"]))
                .label("opportunities"),
            ).where(Insight.status == "published")
        )
        active_sources = await self.session.execute(
            select(func.count(Source.id)).where(Source.status == "active")
        )
        total_row = totals.one()
        return {
            "total": total_row.total or 0,
            "critical_high": total_row.critical_high or 0,
            "opportunities": total_row.opportunities or 0,
            "active_sources": active_sources.scalar_one() or 0,
        }

    def _serialize_insight(self, insight: Insight) -> dict:
        """Convert an ORM object into an API-shaped dictionary."""
        source = insight.raw_document.source
        return {
            "id": insight.id,
            "title": insight.title,
            "summary_short": insight.summary_short,
            "summary_medium": insight.summary_medium,
            "topics": insight.topics,
            "event_type": insight.event_type,
            "nature": insight.nature,
            "trust_score": insight.trust_score,
            "impact_label": insight.impact_label,
            "source_url": insight.source_url,
            "confidence": insight.confidence,
            "status": insight.status,
            "affected_roles": insight.affected_roles or [],
            "published_at": insight.published_at,
            "created_at": insight.created_at,
            "updated_at": insight.updated_at,
            "source_id": source.id,
            "source_name": source.name,
            "source_type": source.source_type,
            "source_feed_url": source.feed_url,
        }
