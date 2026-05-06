"""Insight API routes — list and detail endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.insight_repo import InsightRepository
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.insight import InsightDetail, InsightListItem

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


@router.get("", response_model=PaginatedResponse[InsightListItem])
async def list_insights(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    role: str | None = Query(default=None, description="Filter by affected role (e.g. Engineering)"),
    source_id: uuid.UUID | None = Query(default=None, description="Filter by source UUID"),
    sort_by: str = Query(
        default="created_at",
        description="Sort order: created_at | published_at | impact_label",
        pattern="^(created_at|published_at|impact_label)$",
    ),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[InsightListItem]:
    """Return a paginated list of published insights with optional filters and sort."""
    repo = InsightRepository(session)
    items, total = await repo.list_paginated(
        page=page,
        size=size,
        role=role,
        source_id=source_id,
        sort_by=sort_by,
    )
    return PaginatedResponse(
        page=page,
        size=size,
        total=total,
        items=[InsightListItem.model_validate(item) for item in items],
    )


@router.get(
    "/{insight_id}",
    response_model=InsightDetail,
    responses={404: {"model": ErrorResponse}},
)
async def get_insight(
    insight_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> InsightDetail:
    """Return full detail for a single insight by UUID."""
    repo = InsightRepository(session)
    insight = await repo.get_by_id(insight_id)

    if insight is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": "Insight not found", "code": "INSIGHT_NOT_FOUND"},
        )

    return InsightDetail.model_validate(insight)
