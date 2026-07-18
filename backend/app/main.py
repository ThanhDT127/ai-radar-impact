"""FastAPI application factory."""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.admin import router as admin_router
from app.routes.health import router as health_router
from app.routes.insights import router as insights_router
from app.routes.insights_stats import router as insights_stats_router
from app.routes.sources import router as sources_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi động scheduler nhúng + delivery (bot Telegram) nếu bật.

    LƯU Ý: cả scheduler lẫn delivery không nên chạy kèm --reload
    (job trùng / long-polling trùng → Telegram 409 Conflict).
    """
    scheduler = None
    bot_task = None
    telegram_api = None

    delivery_on = settings.delivery_enabled and bool(settings.telegram_bot_token)
    if settings.delivery_enabled and not settings.telegram_bot_token:
        logger.warning("DELIVERY_ENABLED=true nhưng thiếu TELEGRAM_BOT_TOKEN — delivery bị TẮT")

    if delivery_on:
        from app.bot.handlers import SubscriptionHandlers
        from app.bot.router import UpdateRouter
        from app.bot.worker import TelegramPollingWorker
        from app.channels import ChannelRegistry, TelegramAdapter, TelegramAPI

        telegram_api = TelegramAPI(settings.telegram_bot_token)
        ChannelRegistry.register(TelegramAdapter(telegram_api))
        router = UpdateRouter(telegram_api, SubscriptionHandlers(telegram_api))
        # chatbot-qa đăng ký chat handler qua app.state.bot_router
        app.state.bot_router = router
        bot_task = asyncio.create_task(TelegramPollingWorker(telegram_api, router).run())
        logger.info(
            "Delivery ĐÃ BẬT — bot worker + alert mỗi %d phút + digest %dh (VN)",
            settings.delivery_alert_interval_minutes, settings.delivery_digest_hour,
        )
    else:
        logger.info("Delivery TẮT (DELIVERY_ENABLED=false hoặc thiếu token)")

    if settings.enable_scheduler or delivery_on:
        from app.scheduler import create_scheduler

        scheduler = create_scheduler(
            include_pipeline=settings.enable_scheduler, include_delivery=delivery_on
        )
        scheduler.start()
        if settings.enable_scheduler:
            logger.info(
                "Scheduler ĐÃ BẬT — pipeline giờ (VN): %s, purge %dh30",
                settings.scheduler_hours_list, settings.purge_hour,
            )
        else:
            logger.info("Scheduler pipeline TẮT (ENABLE_SCHEDULER=false) — chỉ chạy delivery jobs")
    else:
        logger.info("Scheduler TẮT (ENABLE_SCHEDULER=false)")

    try:
        yield
    finally:
        if bot_task is not None:
            bot_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await bot_task
        if telegram_api is not None:
            await telegram_api.close()
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title="AI Impact Radar API",
    description="Backend for AI Impact Radar - insight pipeline and delivery",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(insights_stats_router)
app.include_router(insights_router)
app.include_router(sources_router)
app.include_router(admin_router)
