"""Pydantic schemas for Insight API responses."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ActionType = Literal["watch", "read", "test", "PoC", "roadmap"]


class RecommendationItem(BaseModel):
    """A per-role recommendation."""

    action_type: ActionType
    note: str


class InsightReference(BaseModel):
    """A related insight from the same cluster."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source_name: str
    source_url: str


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
    # v2 actionable fields
    signal: str | None = None
    why_it_matters: str | None = None
    recommendations: dict[str, RecommendationItem] | None = None
    risks: list[str] | None = None
    momentum: str | None = None
    urgency: str | None = None
    vietnam_relevance: str | None = None


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
    cluster_id: uuid.UUID | None
    is_primary: bool
    references: list[InsightReference] = []
    # v2 actionable fields
    signal: str | None = None
    why_it_matters: str | None = None
    recommendations: dict[str, RecommendationItem] | None = None
    risks: list[str] | None = None
    momentum: str | None = None
    urgency: str | None = None
    vietnam_relevance: str | None = None
