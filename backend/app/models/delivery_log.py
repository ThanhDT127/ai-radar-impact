"""DeliveryLog model — audit log chống gửi trùng cho delivery engine."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class DeliveryLog(Base):
    """Một lần gửi (insight, chat, kind) — unique để idempotent qua restart."""

    __tablename__ = "delivery_log"
    __table_args__ = (
        UniqueConstraint("insight_id", "chat_id", "kind", name="uq_delivery_log_insight_chat_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insights.id"), nullable=False
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # alert | digest
    sent_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
