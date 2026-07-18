"""Chạy tay delivery engine — alert cycle hoặc digest (không chờ scheduler).

Usage:
    docker-compose exec backend python -m app.scripts.run_delivery --alert
    docker-compose exec backend python -m app.scripts.run_delivery --digest
"""

import argparse
import asyncio
import logging

from app.channels.telegram import TelegramAdapter, TelegramAPI
from app.config import settings
from app.database import async_session_maker
from app.services.delivery_engine import DeliveryEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main(run_alert: bool, run_digest: bool) -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("Thiếu TELEGRAM_BOT_TOKEN — không thể gửi.")

    api = TelegramAPI(settings.telegram_bot_token)
    adapter = TelegramAdapter(api)
    try:
        if run_alert:
            async with async_session_maker() as session:
                result = await DeliveryEngine(session, adapter).run_alert_cycle()
            logger.info("Alert cycle: %s", result)
        if run_digest:
            async with async_session_maker() as session:
                result = await DeliveryEngine(session, adapter).run_digest()
            logger.info("Digest: %s", result)
    finally:
        await api.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy tay delivery alert/digest")
    parser.add_argument("--alert", action="store_true", help="chạy 1 chu kỳ alert")
    parser.add_argument("--digest", action="store_true", help="chạy digest ngay")
    args = parser.parse_args()
    if not (args.alert or args.digest):
        parser.error("chọn --alert và/hoặc --digest")
    asyncio.run(main(args.alert, args.digest))
