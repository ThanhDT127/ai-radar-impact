"""Pydantic schemas for source-oriented responses."""

import uuid

from pydantic import BaseModel


class SourceCreate(BaseModel):
    """Request body for creating a new source."""

    name: str
    source_type: str
    feed_url: str | None = None
    trust_tier: str
    topics: list[str] = []
    status: str = "active"
    config: dict = {}


class SourceListItem(BaseModel):
    """Source row with aggregated insight count."""

    id: uuid.UUID
    name: str
    source_type: str
    status: str
    insight_count: int


class InsightStats(BaseModel):
    """Dashboard KPI stats."""

    total: int
    critical_high: int
    opportunities: int
    active_sources: int
