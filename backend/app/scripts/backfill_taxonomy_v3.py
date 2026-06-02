"""Backfill taxonomy v3 fields for existing insights.

Populates actionability_score and intelligence_tier for insights that have
these columns as NULL. Uses the same rule-based logic as the live pipeline
(gate_score defaults to 0.5 since historical insights bypassed the gate).

Also remaps old topics to the new 12-topic developer-centric taxonomy.

Usage:
    docker-compose exec backend python -m app.scripts.backfill_taxonomy_v3
    docker-compose exec backend python -m app.scripts.backfill_taxonomy_v3 --limit 200
    docker-compose exec backend python -m app.scripts.backfill_taxonomy_v3 --dry-run
"""

import argparse
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.services.analyzer import (
    EVENT_TYPE_WEIGHTS,
    _compute_actionability_score,
    _compute_intelligence_tier,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Old topics → new topics mapping
_TOPIC_REMAP: dict[str, str] = {
    # Vietnamese old taxonomy
    "Trí tuệ nhân tạo": "AI/ML Ứng dụng",
    "AI/ML": "AI/ML Ứng dụng",
    "AI tạo sinh": "AI/ML Ứng dụng",
    "LLM": "AI/ML Ứng dụng",
    "Robotics": "AI/ML Nghiên cứu",
    "Phát triển phần mềm": "DevTools & Frameworks",
    "Công cụ lập trình": "DevTools & Frameworks",
    "Công nghệ": "DevTools & Frameworks",
    "Đám mây": "Cloud & Infrastructure",
    "Cloud": "Cloud & Infrastructure",
    "IoT": "Cloud & Infrastructure",
    "Viễn thông": "Cloud & Infrastructure",
    "Chip & Hardware": "Cloud & Infrastructure",
    "Bảo mật": "Security & Compliance",
    "An ninh mạng": "Security & Compliance",
    "Dữ liệu lớn": "Data Engineering",
    "Big Data": "Data Engineering",
    "Dữ liệu": "Data Engineering",
    "Quy định": "Legal & Regulation",
    "Pháp lý": "Legal & Regulation",
    "Pháp lý/Tuân thủ": "Legal & Regulation",
    "Kinh doanh": "Market & Competition",
    "Startup": "Market & Competition",
    "Thị trường/Đối thủ": "Market & Competition",
    "Thị trường": "Market & Competition",
    "Blockchain": "Platform & API",
    "Dịch vụ/Nền tảng": "Platform & API",
    "API": "Platform & API",
    "Tự động hóa": "Developer Experience",
    "DevOps": "Cloud & Infrastructure",
}

# Valid new topics (for filtering)
_VALID_TOPICS = {
    "AI/ML Ứng dụng",
    "AI/ML Nghiên cứu",
    "DevTools & Frameworks",
    "Cloud & Infrastructure",
    "Data Engineering",
    "Security & Compliance",
    "Software Architecture",
    "Developer Experience",
    "Platform & API",
    "Market & Competition",
    "Legal & Regulation",
    "Team & Process",
}

# Old event types → new event types mapping
_EVENT_TYPE_REMAP: dict[str, str] = {
    "Ngừng hỗ trợ": "Ngừng hỗ trợ/Deprecation",
    "Cập nhật nghiên cứu": "Nghiên cứu/Paper",
}

DEFAULT_GATE_SCORE = 0.5


def _remap_topics(old_topics: list[str]) -> list[str]:
    """Remap old topic names to new taxonomy. Keep valid ones, remap known ones."""
    remapped = []
    seen = set()
    for t in (old_topics or []):
        new_t = _TOPIC_REMAP.get(t, t)
        if new_t in _VALID_TOPICS and new_t not in seen:
            remapped.append(new_t)
            seen.add(new_t)
    if not remapped:
        remapped = ["DevTools & Frameworks"]
    return remapped


def _remap_event_type(old_event_type: str | None) -> str | None:
    if not old_event_type:
        return old_event_type
    return _EVENT_TYPE_REMAP.get(old_event_type, old_event_type)


async def main(limit: int, dry_run: bool) -> None:
    async with async_session_maker() as session:
        query = (
            select(Insight)
            .where(Insight.status == "published")
            .where(Insight.actionability_score.is_(None))
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
            .order_by(Insight.created_at.desc())
            .limit(limit)
        )

        result = await session.execute(query)
        insights = list(result.scalars().unique().all())
        logger.info("Found %d insights to backfill", len(insights))

        updated = 0
        tier_dist: dict[str, int] = {}

        for ins in insights:
            # Remap topics
            old_topics = ins.topics or []
            new_topics = _remap_topics(old_topics)
            topics_changed = old_topics != new_topics

            # Remap event type
            new_event_type = _remap_event_type(ins.event_type)

            # Compute actionability_score with default gate_score
            score = _compute_actionability_score(
                gate_score=DEFAULT_GATE_SCORE,
                confidence=ins.confidence or 0.5,
                trust_score=ins.trust_score or 0.5,
                event_type=new_event_type,
                published_at=ins.published_at,
            )

            # Compute intelligence tier
            tier = _compute_intelligence_tier(score, new_event_type)

            tier_dist[tier] = tier_dist.get(tier, 0) + 1

            if dry_run:
                changes = []
                if topics_changed:
                    changes.append(f"topics: {old_topics} → {new_topics}")
                if new_event_type != ins.event_type:
                    changes.append(f"event_type: {ins.event_type} → {new_event_type}")
                changes.append(f"score={score:.4f} tier={tier}")
                logger.info(
                    "[DRY-RUN] %s: %s | %s",
                    str(ins.id)[:8],
                    ins.title[:60],
                    " | ".join(changes),
                )
            else:
                ins.topics = new_topics
                if new_event_type != ins.event_type:
                    ins.event_type = new_event_type
                ins.actionability_score = score
                ins.intelligence_tier = tier

            updated += 1

        if not dry_run:
            await session.commit()

        logger.info(
            "%s %d insights. Tier distribution: %s",
            "Would update" if dry_run else "Updated",
            updated,
            tier_dist,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill taxonomy v3 fields")
    parser.add_argument("--limit", type=int, default=1000, help="Max insights to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit, dry_run=args.dry_run))
