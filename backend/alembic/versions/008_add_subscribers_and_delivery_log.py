"""add subscribers and delivery_log (delivery-telegram)

Revision ID: 008
Revises: 007
Create Date: 2026-07-17 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscribers",
        sa.Column("chat_id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("roles", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "delivery_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "insight_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("insights.id"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "insight_id", "chat_id", "kind", name="uq_delivery_log_insight_chat_kind"
        ),
    )
    # Quét theo thời gian gửi (trần alert/giờ) và theo chat khi build digest
    op.create_index("idx_delivery_log_sent_at", "delivery_log", ["sent_at"])
    op.create_index("idx_delivery_log_chat_kind", "delivery_log", ["chat_id", "kind"])


def downgrade() -> None:
    op.drop_index("idx_delivery_log_chat_kind", table_name="delivery_log")
    op.drop_index("idx_delivery_log_sent_at", table_name="delivery_log")
    op.drop_table("delivery_log")
    op.drop_table("subscribers")
