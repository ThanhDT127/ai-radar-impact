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
    # Model nhẹ CHỈ để phân loại ý định chat khi luật lưỡng lự (~3,5% câu). Phải là model
    # KHÔNG bật thinking mặc định: đo 25/07/2026, `gemini-2.5-flash` với
    # `max_output_tokens=8` trả text RỖNG vì thinking ăn sạch ngân sách, còn
    # `gemini-2.5-flash-lite` trả đúng nhãn. Đây cũng là model lite duy nhất khả dụng
    # trong us-central1 của project này (2.0-flash-lite → 404).
    intent_classifier_model_id: str = "gemini-2.5-flash-lite"
    # Đặt "" để tắt tầng 2 → chỉ dùng luật tất định (lưỡng lự thì đi pipeline).
    intent_classifier_enabled: bool = True
    # Embedding cho retrieval lai (chat-hybrid-retrieval). Multilingual, KHÔNG phải
    # `text-embedding-004` thiên tiếng Anh: corpus trộn Việt–Anh kỹ thuật. Chiều 768 chốt
    # cứng trong schema (`Insight.EMBEDDING_DIM`) — đổi model ở đây mà khác chiều thì phải
    # đổi cột + backfill lại, không phải đổi một dòng env.
    embedding_model_id: str = "text-multilingual-embedding-002"
    # Tắt tầng vector (retrieval rơi hoàn toàn về lexical). Van xả khi Vertex embedding sự
    # cố kéo dài — chat vẫn chạy, chỉ kém ngữ nghĩa (design D6).
    chat_embedding_enabled: bool = True

    # Server
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # Cost controls
    min_content_length: int = 200
    # ⚠️ ĐƠN VỊ ĐO KHÁC NHAU giữa hai budget dưới đây:
    #   max_daily_analysis  đếm TÀI LIỆU — 1 tài liệu = gate call + analyze call = 2 lượt
    #                       gọi model, nên 500 "đơn vị" thực chất tới ~1000 lượt gọi.
    #   max_daily_chat_calls đếm LƯỢT GỌI model.
    # Đừng so trực tiếp hai con số này với nhau.
    max_daily_analysis: int = 500

    # Document lifecycle (W1 quota guard)
    # Bài published cũ hơn ngưỡng này không vào pipeline phân tích (freshness gate).
    max_age_months: int = 6
    # Insight/tài liệu quá hạn này bị tombstone-purge (giữ fingerprint).
    retention_months: int = 6

    # Scheduler (W1 auto-operation) — mặc định TẮT; chỉ bật ở production (KHÔNG --reload).
    enable_scheduler: bool = False
    scheduler_hours: str = "7,13,19"  # giờ VN (Asia/Ho_Chi_Minh) chạy ingest+analysis mỗi ngày
    purge_hour: int = 3               # giờ VN chạy tombstone-purge hằng ngày
    # Rate-limit tránh 429/403
    ingest_source_delay_seconds: float = 1.0   # delay cố định giữa các nguồn
    ingest_jitter_seconds: float = 2.0         # jitter ngẫu nhiên cộng thêm
    ingest_article_delay_seconds: float = 2.0  # delay giữa các bài TRONG một phiên (Playwright/MXH)
    fetch_max_retries: int = 3                  # số lần thử lại khi fetch lỗi
    fetch_backoff_base_seconds: float = 2.0     # cơ số exponential backoff

    # Anti-bot crawl (W3) — CloakBrowser CDP endpoint.
    # Rỗng = bỏ qua CloakBrowser, dùng Chromium local trực tiếp (dùng cho PoC A/B).
    cloak_cdp_url: str = "http://cloak:9222"

    # Content gate (two-pass pipeline)
    enable_gate: bool = True
    gate_threshold: float = 0.4

    # Delivery (M7) — bản tin định kỳ qua email. Mặc định TẮT; bật sau khi
    # `run_delivery --dry-run` cho kết quả đúng.
    delivery_enabled: bool = False
    delivery_channel: str = "email"
    delivery_digest_hour: int = 8                # giờ VN (Asia/Ho_Chi_Minh) gửi bản tin
    delivery_digest_days: str = "mon,thu"        # ngày trong tuần gửi bản tin
    delivery_digest_lookback_hours: int = 108    # 4.5 ngày — rộng hơn khoảng cách 2 kỳ + đệm
    delivery_max_items_per_role: int = 2         # trần tin mỗi vai trò
    delivery_max_items_per_email: int = 3        # trần tin mỗi email (áp lên tổng)
    delivery_min_gap_hours: int = 48             # chốt chặn: không gửi lại trong ngần này giờ
    dashboard_base_url: str = "http://localhost:5173"  # gốc link "đọc chi tiết" trong email
    public_api_base_url: str = "http://localhost:8000"  # gốc link hủy nhận (backend)

    # SMTP (Gmail App Password) — credential đọc từ env, không nằm trong repo
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_from_name: str = "AI Radar"
    email_reply_to: str = ""

    # Chat Q&A (M8) — consumer Gemini thứ hai, budget TÁCH BIỆT khỏi analysis.
    # Đơn vị: LƯỢT GỌI model (xem ghi chú ở max_daily_analysis).
    # Dashboard không có auth nên quota là hàng rào duy nhất → để khiêm tốn.
    max_daily_chat_calls: int = 200
    # Cửa sổ thời gian dựng index cho chế độ toàn cục. 0 = không giới hạn (cả corpus).
    # Van xả PHỤ: hạ dần 0 → 90 → 30 nếu cần lọc theo độ mới.
    chat_window_days: int = 0
    # Trần số tin đưa vào index sau khi xếp hạng — van xả CHÍNH.
    # Câu trả lời chỉ trích tối đa 5 tin, nên gửi cả kho để chọn ra 5 là lãng phí.
    # Đo 22/07/2026 cùng một câu hỏi: 179 tin → 19.126 input + 3.930 thinking, 23,0s,
    # $0,0160; 60 tin → 6.670 input + 2.534 thinking, 15,0s, $0,0090 (−44% chi phí,
    # −35% thời gian). Cắt theo THỨ HẠNG nên chi phí phẳng khi corpus phình, khác
    # `chat_window_days` cắt theo thời gian. 0 = không giới hạn.
    chat_index_top_k: int = 60

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
