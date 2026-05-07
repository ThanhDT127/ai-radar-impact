"""Pydantic schemas for Insight API responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InsightListItem(BaseModel):
    """Lightweight insight for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    summary_short: str | None
    summary_medium: str | None
    topics: list[str]
    event_type: str | None
    nature: str | None
    trust_score: float
    impact_label: str | None
    source_url: str
    confidence: float
    affected_roles: list[str]
    published_at: datetime | None
    created_at: datetime
    source_id: uuid.UUID
    source_name: str
    source_type: str


class InsightDetail(BaseModel):
    """Full insight detail."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    summary_short: str | None
    summary_medium: str | None
    topics: list[str]
    event_type: str | None
    nature: str | None
    trust_score: float
    impact_label: str | None
    source_url: str
    confidence: float
    status: str
    affected_roles: list[str]
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    source_id: uuid.UUID
    source_name: str
    source_type: str
    source_feed_url: str | None
