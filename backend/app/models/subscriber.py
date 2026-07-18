"""Subscriber model — người nhận tin qua kênh chat (Telegram chat_id)."""

from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Subscriber(Base):
    """Đăng ký nhận tin theo role; định danh bằng Telegram chat_id.

    Bản ghi được tạo ngay từ /start (roles rỗng) — vừa là trạng thái đăng ký,
    vừa là dấu vết "chat đã /start" cho các consumer khác (chatbot Q&A).
    """

    __tablename__ = "subscribers"

    # Telegram chat_id có thể âm (group) và vượt int32 → BigInteger
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
