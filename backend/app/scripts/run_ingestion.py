"""CLI script to run the RSS ingestion pipeline.

Usage (inside Docker container):
    python -m app.scripts.run_ingestion
    python -m app.scripts.run_ingestion --source-id <UUID>
"""

import argparse
import asyncio
import logging
import uuid

from app.database import async_session_maker
from app.services.ingestion import IngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AI Radar ingestion pipeline")
    parser.add_argument(
        "--source-id",
        type=str,
        default=None,
        help="UUID of a specific source to ingest (default: all active sources)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    source_id: uuid.UUID | None = None
    if args.source_id:
        try:
            source_id = uuid.UUID(args.source_id)
        except ValueError:
            logger.error("Invalid source-id: %s", args.source_id)
            return

    async with async_session_maker() as session:
        service = IngestionService(session)
        summary = await service.run(source_id=source_id)

    logger.info(
        "Done — %d new, %d skipped, %d errors",
        summary.new, summary.skipped, summary.errors,
    )


if __name__ == "__main__":
    asyncio.run(main())
