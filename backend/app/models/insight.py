"""Insight model — AI-analyzed intelligence insight."""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, ForeignKey, JSON, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Insight(Base):
    """An AI-analyzed insight derived from a raw document."""

    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_documents.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary_short: Mapped[str | None] = mapped_column(String(300), nullable=True)
    summary_medium: Mapped[str | None] = mapped_column(Text, nullable=True)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    nature: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_label: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="published")
    ai_raw_response: Mapped[dict] = mapped_column(JSON, default=dict)
    # New in v2: roles affected by this insight
    affected_roles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=True)
    # New in v2: original publish date from source (may differ from created_at)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    # Semantic dedup clustering
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    raw_document: Mapped["RawDocument"] = relationship(  # noqa: F821
        "RawDocument", back_populates="insight"
    )
