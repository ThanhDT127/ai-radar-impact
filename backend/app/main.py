"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.admin import router as admin_router
from app.routes.health import router as health_router
from app.routes.insights import router as insights_router
from app.routes.insights_stats import router as insights_stats_router
from app.routes.sources import router as sources_router

app = FastAPI(
    title="AI Impact Radar API",
    description="Backend for AI Impact Radar - insight pipeline and delivery",
    version="0.1.0",
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
