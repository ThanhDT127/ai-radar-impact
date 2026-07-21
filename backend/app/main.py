"""FastAPI application factory."""

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
from app.routes.subscribers import router as subscribers_router
from app.routes.subscribers import unsubscribe_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi động scheduler nhúng (pipeline) nếu bật.

    Delivery job bật/tắt theo DELIVERY_ENABLED — mặc định tắt để migration xong không
    tự bắn mail; bật tay sau khi `run_delivery --dry-run` cho kết quả đúng.
    LƯU Ý: scheduler không nên chạy kèm --reload (job trùng).
    """
    scheduler = None

    if settings.enable_scheduler:
        from app.scheduler import create_scheduler

        scheduler = create_scheduler(
            include_pipeline=True, include_delivery=settings.delivery_enabled
        )
        scheduler.start()
        logger.info(
            "Scheduler ĐÃ BẬT — pipeline giờ (VN): %s, purge %dh30",
            settings.scheduler_hours_list, settings.purge_hour,
        )
    else:
        logger.info("Scheduler TẮT (ENABLE_SCHEDULER=false)")

    try:
        yield
    finally:
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
app.include_router(subscribers_router)
app.include_router(unsubscribe_router)
