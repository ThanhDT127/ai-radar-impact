"""DocumentChunk model — đoạn thân bài kèm embedding, dùng cho TẦNG XẾP HẠNG của chat.

⚠️ Ranh giới quan trọng nhất của bảng này: **đoạn XẾP HẠNG, insight TRÍCH DẪN**. Đoạn không
bao giờ xuất hiện trong prompt như một mục nguồn được đánh số, và bảng ánh xạ `n → nguồn` chỉ
trỏ tới insight. Cho đoạn thành nguồn trích dẫn là dựng lại cái bẫy "hai hệ quy chiếu cho `n`"
mà `chat-citation-integrity` đã trả giá một lần, ở quy mô lớn hơn (một bài 5 đoạn ⇒ 5 số cho
cùng một nguồn).
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.insight import EMBEDDING_DIM


class DocumentChunk(Base):
    """Một đoạn của `raw_documents.normalized_content`."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("raw_document_id", "ordinal", name="uq_document_chunks_doc_ordinal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_documents.id", ondelete="CASCADE"), nullable=False
    )
    # NULLABLE có chủ đích: ingest chạy trước analyze, nên đoạn có thể tồn tại trước insight.
    # Nối lại lúc publish. Đoạn `insight_id IS NULL` không tham gia xếp hạng (không có tin để
    # gán thứ hạng cho) — nó chỉ đang chờ.
    insight_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insights.id", ondelete="CASCADE"), nullable=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # NULL = embed lỗi lúc sinh. Trạng thái HỢP LỆ, không phải dữ liệu hỏng: `_rank` cho tin
    # thiếu tín hiệu đoạn mượn thứ hạng vector của chính nó thay vì phạt ngầm.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    raw_document: Mapped["RawDocument"] = relationship(  # noqa: F821
        "RawDocument", back_populates="chunks"
    )
    insight: Mapped["Insight | None"] = relationship(  # noqa: F821
        "Insight", back_populates="chunks"
    )
