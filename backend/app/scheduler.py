"""Scheduler nhúng (APScheduler) cho tự động hoá pipeline — W1 auto-operation.

Chạy ingest → analysis 2–4 lần/ngày + tombstone-purge hằng ngày. Mặc định TẮT
(`ENABLE_SCHEDULER=false`); chỉ bật ở production và KHÔNG chạy kèm `--reload`
để tránh chạy trùng job.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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


def create_scheduler() -> AsyncIOScheduler:
    """Tạo scheduler với các job ingest+analysis và purge (chưa start)."""
    scheduler = AsyncIOScheduler(timezone="UTC")

    for hour in settings.scheduler_hours_list:
        scheduler.add_job(
            scheduled_pipeline,
            trigger=CronTrigger(hour=hour, minute=0),
            id=f"pipeline_{hour}",
            max_instances=1,   # không chạy chồng lấn
            coalesce=True,     # gộp nếu lỡ nhiều lần dồn lại
            misfire_grace_time=3600,
        )

    scheduler.add_job(
        scheduled_purge,
        trigger=CronTrigger(hour=settings.purge_hour, minute=30),
        id="purge_expired",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    return scheduler
