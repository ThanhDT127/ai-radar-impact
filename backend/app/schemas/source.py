"""Pydantic schemas for source-oriented responses."""

import uuid

from pydantic import BaseModel


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
