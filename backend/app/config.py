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


settings = Settings()
