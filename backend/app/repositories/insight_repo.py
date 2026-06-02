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

# Urgency sort order: critical → high → medium → low → null/unknown
_URGENCY_ORDER = case(
    (Insight.urgency == "critical", 1),
    (Insight.urgency == "high", 2),
    (Insight.urgency == "medium", 3),
    (Insight.urgency == "low", 4),
    else_=5,
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
        signal: str | None = None,
        why_it_matters: str | None = None,
        recommendations: dict | None = None,
        risks: list[str] | None = None,
        urgency: str | None = None,
        vietnam_relevance: str | None = None,
        actionability_score: float | None = None,
        intelligence_tier: str | None = None,
        so_what: str | None = None,
        adoption_ring: str | None = None,
        practical_indicators: dict | None = None,
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
            signal=signal,
            why_it_matters=why_it_matters,
            recommendations=recommendations,
            risks=risks,
            urgency=urgency,
            vietnam_relevance=vietnam_relevance,
            actionability_score=actionability_score,
            intelligence_tier=intelligence_tier,
            so_what=so_what,
            adoption_ring=adoption_ring,
            practical_indicators=practical_indicators,
        )
        self.session.add(insight)
        await self.session.flush()
        return insight

    async def update_momentum(self, insight_id: uuid.UUID, momentum: str) -> None:
        """Update momentum for a single insight (called post-dedup)."""
        result = await self.session.execute(
            select(Insight).where(Insight.id == insight_id)
        )
        insight = result.scalar_one_or_none()
        if insight is not None:
            insight.momentum = momentum

    async def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        roles: list[str] | None = None,
        source_ids: list[uuid.UUID] | None = None,
        sort_by: str = "urgency",
        urgency: list[str] | None = None,
        momentum: list[str] | None = None,
        vietnam_relevance: list[str] | None = None,
        intelligence_tier: list[str] | None = None,
    ) -> tuple[list[dict], int]:
        """Return paginated insights with optional role/source filters and sort."""
        offset = (page - 1) * size

        base_query = (
            select(Insight)
            .join(RawDocument, Insight.raw_document_id == RawDocument.id)
            .join(Source, RawDocument.source_id == Source.id)
            .where(Insight.status == "published")
            .where(Insight.is_primary == True)  # noqa: E712
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
        )

        if roles:
            base_query = base_query.where(
                or_(*(Insight.affected_roles.any(role) for role in roles))
            )

        if source_ids:
            base_query = base_query.where(RawDocument.source_id.in_(source_ids))

        if urgency:
            base_query = base_query.where(Insight.urgency.in_(urgency))
        if momentum:
            base_query = base_query.where(Insight.momentum.in_(momentum))
        if vietnam_relevance:
            base_query = base_query.where(Insight.vietnam_relevance.in_(vietnam_relevance))
        if intelligence_tier:
            base_query = base_query.where(Insight.intelligence_tier.in_(intelligence_tier))

        if sort_by == "published_at":
            order = (Insight.published_at.desc().nulls_last(),)
        elif sort_by == "impact_label":
            order = (_IMPACT_ORDER.asc(),)
        elif sort_by == "trust_score":
            order = (Insight.trust_score.desc().nulls_last(),)
        elif sort_by == "created_at":
            order = (Insight.created_at.desc(),)
        elif sort_by == "actionability_score":
            order = (Insight.actionability_score.desc().nulls_last(),)
        else:
            # Default: urgency (critical→low) THEN published_at DESC
            order = (_URGENCY_ORDER.asc(), Insight.published_at.desc().nulls_last())

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            base_query.order_by(*order).offset(offset).limit(size)
        )
        items = [self._serialize_insight(item) for item in result.scalars().unique().all()]
        return items, total

    async def get_by_id(self, insight_id: uuid.UUID) -> dict | None:
        """Return a single insight by UUID with references, or None."""
        result = await self.session.execute(
            select(Insight)
            .where(Insight.id == insight_id)
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
        )
        insight = result.scalar_one_or_none()
        if insight is None:
            return None

        references: list[dict] = []
        if insight.cluster_id is not None:
            ref_result = await self.session.execute(
                select(Insight, Source.name.label("source_name"))
                .join(RawDocument, Insight.raw_document_id == RawDocument.id)
                .join(Source, RawDocument.source_id == Source.id)
                .where(Insight.cluster_id == insight.cluster_id)
                .where(Insight.id != insight_id)
                .where(Insight.status == "published")
            )
            for ref_insight, src_name in ref_result:
                references.append({
                    "id": ref_insight.id,
                    "title": ref_insight.title,
                    "source_name": src_name,
                    "source_url": ref_insight.source_url,
                })

        return self._serialize_insight(insight, references=references)

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

    def _serialize_insight(self, insight: Insight, references: list[dict] | None = None) -> dict:
        """Convert an ORM object into an API-shaped dictionary."""
        # Dynamically extract primary image URL from raw_content or metadata
        primary_image = None
        raw_content = insight.raw_document.raw_content or ""
        metadata = insight.raw_document.metadata_ or {}
        
        if "primary_image_url" in metadata:
            primary_image = metadata["primary_image_url"]
            
        if not primary_image and raw_content:
            import re
            og_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', raw_content, re.IGNORECASE)
            if og_match:
                primary_image = og_match.group(1)
            else:
                tw_match = re.search(r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']', raw_content, re.IGNORECASE)
                if tw_match:
                    primary_image = tw_match.group(1)
                else:
                    img_match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\']', raw_content, re.IGNORECASE)
                    if img_match:
                        img_src = img_match.group(1)
                        if "pixel" not in img_src.lower() and "logo" not in img_src.lower() and not img_src.startswith("data:"):
                            primary_image = img_src

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
            "cluster_id": insight.cluster_id,
            "is_primary": insight.is_primary,
            "references": references or [],
            "signal": insight.signal,
            "why_it_matters": insight.why_it_matters,
            "recommendations": insight.recommendations,
            "risks": insight.risks,
            "momentum": insight.momentum,
            "urgency": insight.urgency,
            "vietnam_relevance": insight.vietnam_relevance,
            "actionability_score": insight.actionability_score,
            "intelligence_tier": insight.intelligence_tier,
            "so_what": insight.so_what,
            "adoption_ring": insight.adoption_ring,
            "practical_indicators": insight.practical_indicators,
            "content_text": insight.raw_document.normalized_content or insight.raw_document.raw_content,
            "primary_image": primary_image,
        }
