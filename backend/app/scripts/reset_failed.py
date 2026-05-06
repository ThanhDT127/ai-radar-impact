"""Reset failed raw_documents back to pending status for re-analysis.

Usage:
    docker-compose exec backend python -m app.scripts.reset_failed
"""

import asyncio
import logging

from sqlalchemy import update

from app.database import async_session_maker
from app.models.raw_document import RawDocument

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def reset() -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            update(RawDocument)
            .where(RawDocument.processing_status == "failed")
            .values(processing_status="pending")
            .returning(RawDocument.id)
        )
        rows = result.fetchall()
        await session.commit()
        logger.info("Reset %d document(s) from 'failed' → 'pending'", len(rows))


if __name__ == "__main__":
    asyncio.run(reset())
