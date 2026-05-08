"""Run semantic deduplication on recent insights.

Usage:
    docker-compose exec backend python -m app.scripts.run_dedup
"""

import asyncio
import logging

from app.database import async_session_maker
from app.services.dedup_engine import DeduplicationEngine

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    async with async_session_maker() as session:
        engine = DeduplicationEngine(session)
        result = await engine.run_dedup()
    logger.info("Done — %s", result)


if __name__ == "__main__":
    asyncio.run(main())
