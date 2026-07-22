"""add chat_logs (chatbot-qa)

Revision ID: 011
Revises: 010
Create Date: 2026-07-22 03:00:00.000000

Bảng log request chat, đồng thời là counter budget `max_daily_chat_calls`
(tổng `model_calls` trong ngày UTC). Index trên `created_at` phục vụ đúng truy vấn đó.

Không lưu nội dung câu hỏi/trả lời — v1 chỉ metadata.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("model_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("citations_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_chat_logs_created_at", "chat_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_chat_logs_created_at", table_name="chat_logs")
    op.drop_table("chat_logs")
