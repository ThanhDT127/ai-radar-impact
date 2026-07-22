"""ChatLog model — log mỗi request chat, ĐỒNG THỜI là counter quota.

Không tách bảng counter riêng: budget dùng trong ngày = tổng `model_calls` của các bản
ghi trong ngày (UTC). Cùng lý do như `raw_documents.analyzed_at` bên analysis — đếm
bằng DB nên đúng xuyên nhiều tiến trình và sống sót qua restart.

KHÔNG lưu nội dung câu hỏi/câu trả lời (quyết định design: chỉ metadata ở v1).
"""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mode: Mapped[str] = mapped_column(String(10), nullable=False)  # insight | global
    model_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    citations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
