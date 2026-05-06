"""Common Pydantic response schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response."""

    page: int
    size: int
    total: int
    items: list[T]


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str
    code: str
