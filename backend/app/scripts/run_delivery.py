"""Chạy tay một kỳ bản tin (M7 Delivery).

Usage:
    docker-compose exec backend python -m app.scripts.run_delivery --dry-run
    docker-compose exec backend python -m app.scripts.run_delivery --send

`--dry-run` in nội dung ra stdout, KHÔNG gửi và KHÔNG ghi delivery_log — dùng để đối
chiếu số tin mỗi vai trò với trần trước khi bật gửi thật.
"""

import argparse
import asyncio
import logging

import app.channels  # noqa: F401 — import để EmailAdapter tự đăng ký vào registry
from app.channels.base import ChannelRegistry
from app.config import settings
from app.database import async_session_maker
from app.services.delivery_engine import DeliveryEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def quiet_sql_echo() -> None:
    """Tắt echo SQL của engine — nếu không, nội dung bản tin bị nhấn chìm.

    Phải gọi SAU khi `app.database` tạo engine: `echo=True` tự đặt logger về INFO lúc
    tạo engine, nên hạ level ở đầu module sẽ bị ghi đè.
    """
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)


async def main(dry_run: bool, force: bool) -> None:
    quiet_sql_echo()
    adapter = ChannelRegistry.get(settings.delivery_channel)
    async with async_session_maker() as session:
        engine = DeliveryEngine(session, adapter)
        result = await engine.run_brief(dry_run=dry_run, force=force)
    logger.info(
        "Kỳ bản tin xong — sent=%d failed=%d skipped=%d%s",
        result["sent"], result["failed"], result["skipped"],
        " (DRY RUN — không gửi, không ghi log)" if dry_run else "",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy một kỳ bản tin AI Radar")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="in nội dung, không gửi")
    group.add_argument("--send", action="store_true", help="gửi thật")
    parser.add_argument(
        "--force",
        action="store_true",
        help="bỏ qua chốt chặn chu kỳ (DELIVERY_MIN_GAP_HOURS) — chỉ dùng khi test",
    )
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run, force=args.force))
