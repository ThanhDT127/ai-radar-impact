"""Source model — whitelisted intelligence sources."""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Source(Base):
    """A whitelisted intelligence source (RSS feed, API, web page)."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # rss, api, web
    feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    trust_tier: Mapped[str] = mapped_column(String(20), nullable=False)  # very_high, high, medium, low
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    raw_documents: Mapped[list["RawDocument"]] = relationship(  # noqa: F821
        "RawDocument", back_populates="source"
    )
