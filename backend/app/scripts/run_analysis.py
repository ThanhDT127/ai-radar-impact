"""Run AI analysis on all pending raw_documents.

Usage:
    docker-compose exec backend python -m app.scripts.run_analysis
"""

import asyncio
import logging

from app.database import async_session_maker
from app.services.analyzer import AnalyzerService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    async with async_session_maker() as session:
        analyzer = AnalyzerService(session)
        counts = await analyzer.run_pending()
        logger.info(
            "Analysis complete — created: %d, skipped: %d, errors: %d",
            counts.get("created", 0),
            counts.get("skipped", 0),
            counts.get("errors", 0),
        )


if __name__ == "__main__":
    asyncio.run(main())
