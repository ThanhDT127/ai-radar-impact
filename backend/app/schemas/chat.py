"""Pydantic schemas cho endpoint chat Q&A."""

import uuid

from pydantic import BaseModel, Field, field_validator

# History do client giữ (service stateless). Cap ở đây thay vì tin client tự cắt.
MAX_HISTORY_TURNS = 10


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role phải là 'user' hoặc 'assistant'")
        return v


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = []
    insight_id: uuid.UUID | None = None

    @field_validator("history")
    @classmethod
    def cap_history(cls, v: list[ChatTurn]) -> list[ChatTurn]:
        """Giữ 10 lượt GẦN NHẤT — cắt đuôi trước, không phải cắt đầu."""
        return v[-MAX_HISTORY_TURNS:]


class Citation(BaseModel):
    insight_id: uuid.UUID
    title: str
    source_url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    mode: str  # "insight" | "global" | "meta" | "expanded"
