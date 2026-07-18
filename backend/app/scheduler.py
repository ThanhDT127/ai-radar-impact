"""Scheduler nhúng (APScheduler) cho tự động hoá pipeline — W1 auto-operation.

Chạy ingest → analysis 2–4 lần/ngày + tombstone-purge hằng ngày. Mặc định TẮT
(`ENABLE_SCHEDULER=false`); chỉ bật ở production và KHÔNG chạy kèm `--reload`
để tránh chạy trùng job.

MỌI giờ cron đều theo giờ VN (`Asia/Ho_Chi_Minh`). LƯU Ý: `CronTrigger(hour=...)`
dựng sẵn KHÔNG kế thừa timezone của scheduler — phải truyền `timezone="Asia/Ho_Chi_Minh"`
thẳng vào từng trigger, nếu không nó rơi về localzone container (UTC).
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import async_session_maker
from app.scripts.purge_expired import purge_expired
from app.services.analyzer import AnalyzerService
from app.services.ingestion import IngestionService

logger = logging.getLogger(__name__)


async def scheduled_pipeline() -> None:
    """Cào toàn bộ nguồn active rồi phân tích (drain backlog trong daily cap)."""
    logger.info("[scheduler] Bắt đầu chu kỳ ingest+analysis")
    async with async_session_maker() as session:
        summary = await IngestionService(session).run()
    # Drain thêm backlog pending kể cả khi không có tin mới (vẫn tôn trọng cap DB).
    async with async_session_maker() as session:
        await AnalyzerService(session).run_pending()
    logger.info(
        "[scheduler] Xong chu kỳ — new=%d skipped_old=%d insights=%d",
        summary.new, summary.skipped_old, summary.insights_created,
    )


async def scheduled_purge() -> None:
    """Tombstone-purge insight/doc quá hạn retention."""
    logger.info("[scheduler] Bắt đầu tombstone-purge")
    async with async_session_maker() as session:
        await purge_expired(session)


async def scheduled_alert_cycle() -> None:
    """Quét insight critical mới → alert Telegram (M7 Delivery)."""
    from app.channels.base import ChannelRegistry
    from app.services.delivery_engine import DeliveryEngine

    async with async_session_maker() as session:
        await DeliveryEngine(session, ChannelRegistry.get("telegram")).run_alert_cycle()


async def scheduled_digest() -> None:
    """Digest hằng ngày (M7 Delivery)."""
    from app.channels.base import ChannelRegistry
    from app.services.delivery_engine import DeliveryEngine

    logger.info("[scheduler] Bắt đầu digest hằng ngày")
    async with async_session_maker() as session:
        await DeliveryEngine(session, ChannelRegistry.get("telegram")).run_digest()


def create_scheduler(include_pipeline: bool = True, include_delivery: bool = False) -> AsyncIOScheduler:
    """Tạo scheduler (chưa start): pipeline/purge và/hoặc delivery jobs."""
    scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")

    if include_pipeline:
        for hour in settings.scheduler_hours_list:
            scheduler.add_job(
                scheduled_pipeline,
                trigger=CronTrigger(hour=hour, minute=0, timezone="Asia/Ho_Chi_Minh"),
                id=f"pipeline_{hour}",
                max_instances=1,   # không chạy chồng lấn
                coalesce=True,     # gộp nếu lỡ nhiều lần dồn lại
                misfire_grace_time=3600,
            )

        scheduler.add_job(
            scheduled_purge,
            trigger=CronTrigger(hour=settings.purge_hour, minute=30, timezone="Asia/Ho_Chi_Minh"),
            id="purge_expired",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )

    if include_delivery:
        scheduler.add_job(
            scheduled_alert_cycle,
            trigger=IntervalTrigger(minutes=settings.delivery_alert_interval_minutes),
            id="delivery_alert_cycle",
            max_instances=1,
            coalesce=True,
        )
        # Giờ digest theo giờ VN (D3) — như mọi cron khác trong file này
        scheduler.add_job(
            scheduled_digest,
            trigger=CronTrigger(
                hour=settings.delivery_digest_hour, minute=0, timezone="Asia/Ho_Chi_Minh"
            ),
            id="delivery_digest",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )

    return scheduler
