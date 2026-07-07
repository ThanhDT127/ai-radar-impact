"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],  # search both /app/.env and parent
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://radar:radar_dev@db:5432/ai_radar"

    # AI — Vertex AI
    google_cloud_project: str = "omega-dahlia-475002-r7"
    google_cloud_location: str = "us-central1"
    google_genai_use_vertexai: str = "True"
    gemini_model_id: str = "gemini-2.5-flash"

    # Server
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # Cost controls
    min_content_length: int = 200
    max_daily_analysis: int = 500

    # Document lifecycle (W1 quota guard)
    # Bài published cũ hơn ngưỡng này không vào pipeline phân tích (freshness gate).
    max_age_months: int = 6
    # Insight/tài liệu quá hạn này bị tombstone-purge (giữ fingerprint).
    retention_months: int = 6

    # Scheduler (W1 auto-operation) — mặc định TẮT; chỉ bật ở production (KHÔNG --reload).
    enable_scheduler: bool = False
    scheduler_hours: str = "7,13,19"  # giờ (UTC) chạy ingest+analysis mỗi ngày
    purge_hour: int = 3               # giờ (UTC) chạy tombstone-purge hằng ngày
    # Rate-limit tránh 429/403
    ingest_source_delay_seconds: float = 1.0   # delay cố định giữa các nguồn
    ingest_jitter_seconds: float = 2.0         # jitter ngẫu nhiên cộng thêm
    fetch_max_retries: int = 3                  # số lần thử lại khi fetch lỗi
    fetch_backoff_base_seconds: float = 2.0     # cơ số exponential backoff

    # Content gate (two-pass pipeline)
    enable_gate: bool = True
    gate_threshold: float = 0.4

    # Admin API
    admin_api_key: str = "changeme"

    # Environment
    env: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def scheduler_hours_list(self) -> list[int]:
        """Parse scheduler_hours ('7,13,19') thành list giờ int."""
        return [int(h.strip()) for h in self.scheduler_hours.split(",") if h.strip()]


settings = Settings()
