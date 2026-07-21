"""Pydantic schemas cho quản lý người nhận bản tin."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.ai.prompts import ALLOWED_ROLES

# Kiểm tra hình thức đủ dùng — tránh kéo thêm dependency `email-validator` chỉ để
# validate một ô nhập. Địa chỉ sai thật sẽ lộ ra ở lần gửi đầu (SMTP trả lỗi).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> str:
    value = email.strip().lower()
    if not _EMAIL_RE.match(value):
        raise ValueError("Địa chỉ email không hợp lệ")
    return value


def _validate_roles(roles: list[str]) -> list[str]:
    """Roles phải nằm trong 9 vai trò của `ALLOWED_ROLES` (KHÔNG phải target_roles)."""
    invalid = [r for r in roles if r not in ALLOWED_ROLES]
    if invalid:
        raise ValueError(
            f"Vai trò không hợp lệ: {', '.join(invalid)}. Cho phép: {', '.join(ALLOWED_ROLES)}"
        )
    return roles


class SubscriberCreate(BaseModel):
    email: str
    roles: list[str] = []
    display_name: str | None = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("roles")
    @classmethod
    def check_roles(cls, v: list[str]) -> list[str]:
        return _validate_roles(v)


class SubscriberUpdate(BaseModel):
    roles: list[str] | None = None
    active: bool | None = None
    display_name: str | None = None

    @field_validator("roles")
    @classmethod
    def check_roles(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else _validate_roles(v)


class SubscriberItem(BaseModel):
    id: uuid.UUID
    email: str
    roles: list[str]
    display_name: str | None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
