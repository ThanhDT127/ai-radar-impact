"""DeliveryLog model — audit log chống gửi trùng cho delivery engine."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class DeliveryLog(Base):
    """Một lần gửi (insight, subscriber, kind) — unique để idempotent qua restart.

    Chỉ ghi cho tin THỰC SỰ được gửi. Tin bị loại vì trần số lượng mỗi email không
    ghi log, để còn quyền cạnh tranh ở kỳ kế tiếp nếu vẫn trong lookback.
    """

    __tablename__ = "delivery_log"
    __table_args__ = (
        UniqueConstraint(
            "insight_id", "subscriber_id", "kind",
            name="uq_delivery_log_insight_subscriber_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insights.id"), nullable=False
    )
    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # brief
    sent_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
