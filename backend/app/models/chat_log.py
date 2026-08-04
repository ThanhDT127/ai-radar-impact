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
    # insight | global | meta | expanded (VARCHAR(10) — "expanded" là giá trị dài nhất, 8)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    model_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    citations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Token SUY LUẬN của lượt trả lời. NULL = nhà cung cấp không báo cáo (bản SDK 0.8.0 cũ
    # luôn giấu số này) — KHÁC `0` = đã ghìm về 0 và model tuân thủ. Đừng gộp hai nghĩa.
    thinking_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Số TRUY VẤN tra cứu ngoài. Đếm riêng khỏi `model_calls` vì đơn giá cách nhau bậc:
    # grounding $35/1.000 truy vấn so với ~$0,006 cho cả một câu trả lời. NULL = bản ghi có
    # trước `chat-web-fallback`; 0 = lượt đó thật sự không tra cứu.
    web_searches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
