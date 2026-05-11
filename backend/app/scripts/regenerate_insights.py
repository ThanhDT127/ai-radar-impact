"""Regenerate insights with v2 prompt (signal/why_it_matters/recommendations/risks).

Re-runs Gemini analysis on existing insights so old insights gain the v2 actionable fields.
Existing insight row is overwritten in-place; raw_document is reused.

Usage:
    docker-compose exec backend python -m app.scripts.regenerate_insights --limit 50
    docker-compose exec backend python -m app.scripts.regenerate_insights --since 2026-05-01
    docker-compose exec backend python -m app.scripts.regenerate_insights --source-id <UUID>
"""

import argparse
import asyncio
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai.gemini_client import GeminiClient
from app.database import async_session_maker
from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.services.analyzer import (
    IMPACT_LABEL_MAP,
    TRUST_SCORE_MAP,
    _compute_urgency,
    _compute_vietnam_relevance,
    _validate_recommendations,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main(limit: int, since: str | None, source_id: str | None) -> None:
    gemini = GeminiClient()

    async with async_session_maker() as session:
        query = (
            select(Insight)
            .join(RawDocument, Insight.raw_document_id == RawDocument.id)
            .where(Insight.status == "published")
            .where(Insight.signal.is_(None))
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
            .order_by(Insight.created_at.desc())
            .limit(limit)
        )

        if since:
            since_dt = datetime.fromisoformat(since)
            query = query.where(Insight.created_at >= since_dt)
        if source_id:
            query = query.where(RawDocument.source_id == uuid.UUID(source_id))

        result = await session.execute(query)
        insights = list(result.scalars().unique().all())
        logger.info("Regenerating %d insights", len(insights))

        updated = 0
        for ins in insights:
            raw_doc = ins.raw_document
            source = raw_doc.source
            content = raw_doc.normalized_content or raw_doc.raw_content or ""
            if not content.strip():
                continue

            ai = gemini.analyze(title=raw_doc.title or "", content=content)
            if ai.error:
                logger.warning("Skip insight %s: %s", ins.id, ai.error)
                continue

            impact_label = IMPACT_LABEL_MAP.get(ai.event_type or "", ins.impact_label)
            recs = _validate_recommendations(ai.recommendations, ai.affected_roles)

            ins.summary_short = ai.summary_short or ins.summary_short
            ins.summary_medium = ai.summary_medium or ins.summary_medium
            ins.topics = ai.topics or ins.topics
            ins.event_type = ai.event_type or ins.event_type
            ins.nature = ai.nature or ins.nature
            ins.affected_roles = ai.affected_roles or ins.affected_roles
            ins.confidence = ai.confidence or ins.confidence
            ins.impact_label = impact_label
            ins.trust_score = TRUST_SCORE_MAP.get(source.trust_tier, ins.trust_score)
            ins.ai_raw_response = ai.raw_response
            ins.signal = ai.signal
            ins.why_it_matters = ai.why_it_matters
            ins.recommendations = recs
            ins.risks = ai.risks
            ins.urgency = _compute_urgency(impact_label, raw_doc.published_at)
            ins.vietnam_relevance = _compute_vietnam_relevance(source, ai.topics)
            updated += 1

        await session.commit()
        logger.info("Regenerated %d insights", updated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--since", type=str, default=None, help="ISO date (YYYY-MM-DD)")
    parser.add_argument("--source-id", type=str, default=None)
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit, since=args.since, source_id=args.source_id))
