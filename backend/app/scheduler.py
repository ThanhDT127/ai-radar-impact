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

from app.config import settings
from app.database import async_session_maker
from app.scripts.purge_expired import purge_expired
from app.services.analyzer import AnalyzerService
from app.services.ingestion import IngestionService

logger = logging.getLogger(__name__)

# Key kênh delivery trong ChannelRegistry — `EmailAdapter` tự đăng ký khi import
# `app.channels`.
DELIVERY_CHANNEL = settings.delivery_channel


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


async def scheduled_brief() -> None:
    """Bản tin định kỳ theo vai trò (M7 Delivery, channel-neutral)."""
    import app.channels  # noqa: F401 — import để adapter tự đăng ký vào registry
    from app.channels.base import ChannelRegistry
    from app.services.delivery_engine import DeliveryEngine

    logger.info("[scheduler] Bắt đầu kỳ bản tin")
    async with async_session_maker() as session:
        await DeliveryEngine(session, ChannelRegistry.get(DELIVERY_CHANNEL)).run_brief()


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
        # Cron theo NGÀY TRONG TUẦN (mặc định mon,thu — cách nhau 3–4 ngày nhưng luôn
        # rơi ngày làm việc). KHÔNG dùng IntervalTrigger(days=3): jobstore trong bộ nhớ
        # nên mỗi lần restart mốc kế tiếp tính lại từ đầu ⇒ nhịp trôi dạt. Cũng KHÔNG
        # dùng day='*/3' (ngày-trong-tháng, nhảy sai ở ranh giới tháng).
        scheduler.add_job(
            scheduled_brief,
            trigger=CronTrigger(
                day_of_week=settings.delivery_digest_days,
                hour=settings.delivery_digest_hour,
                minute=0,
                timezone="Asia/Ho_Chi_Minh",
            ),
            id="delivery_brief",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )

    return scheduler
