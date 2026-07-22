"""Tombstone-purge insights/raw_documents quá hạn retention (W1 quota guard).

Quá `retention_months` (mặc định 6): ẩn insight (status='expired'), xóa content
nặng của raw_document nhưng GIỮ `fingerprint` → crawl lại về sau vẫn bị dedup
skip, KHÔNG phân tích lại → không tốn quota Gemini. KHÔNG hard-delete.

Usage:
    docker-compose exec backend python -m app.scripts.purge_expired
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.repositories.insight_repo import InsightRepository
from app.repositories.raw_document_repo import RawDocumentRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Xấp xỉ 1 tháng = 30 ngày (khớp freshness gate trong ingestion).
DAYS_PER_MONTH = 30


async def purge_expired(session: AsyncSession) -> dict[str, int]:
    """Chạy tombstone-purge trong 1 session. Trả về counts."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=settings.retention_months * DAYS_PER_MONTH)

    # Ẩn insight trước (khớp thứ tự spec; soft-purge nên FK không ảnh hưởng).
    insights_expired = await InsightRepository(session).expire_older_than(cutoff)
    docs_tombstoned = await RawDocumentRepository(session).tombstone_older_than(cutoff)
    await session.commit()

    counts = {"insights_expired": insights_expired, "docs_tombstoned": docs_tombstoned}
    logger.info(
        "Purge complete (cutoff=%s) — insights expired: %d, docs tombstoned: %d",
        cutoff.date(), insights_expired, docs_tombstoned,
    )
    return counts


async def main() -> None:
    async with async_session_maker() as session:
        await purge_expired(session)


if __name__ == "__main__":
    asyncio.run(main())
