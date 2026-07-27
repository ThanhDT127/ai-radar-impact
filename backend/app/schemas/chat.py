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
    """Một nguồn được trích dẫn, kèm CHÍNH con số marker đã xuất hiện trong answer.

    `n` là số thứ tự trong index do server cấp phát (1..N), **không** phải vị trí trong mảng
    này. Hai hệ quy chiếu đó chỉ trùng nhau khi model trích dẫn liền mạch từ [1] — và nó
    thường làm vậy chỉ vì prompt dặn "tin ở đầu danh sách đáng chọn hơn". Client cũ suy `n`
    từ vị trí mảng (`citations[n-1]`) nên trỏ sai ngay khi model bỏ qua một tin ở giữa; tức
    là lỗi bị che bởi chất lượng xếp hạng và sẽ lộ ra đúng lúc xếp hạng kém đi.
    Đưa `n` thành dữ liệu để ranh giới backend↔frontend tự mô tả, không phải cùng đoán đúng.
    """

    n: int
    insight_id: uuid.UUID
    title: str
    source_url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    mode: str  # "insight" | "global" | "meta" | "expanded"
