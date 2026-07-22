"""Subscriber model — người nhận bản tin qua email, lọc nội dung theo role."""

import secrets
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


def new_unsubscribe_token() -> str:
    """Token bí mật cho link hủy nhận (43 ký tự urlsafe)."""
    return secrets.token_urlsafe(32)


class Subscriber(Base):
    """Đăng ký nhận bản tin theo role; định danh bằng địa chỉ email.

    `email` lưu dạng lowercase đã normalize để so trùng không phụ thuộc hoa/thường.
    Hủy nhận đặt `active = False` chứ không xoá bản ghi, để giữ lịch sử delivery_log.
    """

    __tablename__ = "subscribers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    unsubscribe_token: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, default=new_unsubscribe_token
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
