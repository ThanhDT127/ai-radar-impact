"""RawDocument model — raw content fetched from sources."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import false, func

from app.database import Base


class RawDocument(Base):
    """Raw content fetched from a source, before AI analysis."""

    __tablename__ = "raw_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    processing_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, analyzed, low_signal, failed, expired
    # Set khi doc đạt trạng thái terminal (analyzed/low_signal/failed) — dùng đếm daily cap.
    analyzed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    # True khi gate lỗi parse và doc được cho đi thẳng vào deep analysis (fail-open).
    # Thống kê tỉ lệ qua gate PHẢI lọc `gate_skipped == False`, nếu không sẽ đếm cả
    # doc chưa từng được gate chấm. Doc trước 2026-07-20 mang false (không backfill được).
    gate_skipped: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false(), default=False
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="raw_documents")  # noqa: F821
    insight: Mapped["Insight | None"] = relationship("Insight", back_populates="raw_document")  # noqa: F821
