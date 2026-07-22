"""switch subscribers/delivery_log from telegram chat_id to email identity

Revision ID: 010
Revises: 009
Create Date: 2026-07-21 08:00:00.000000

Transport telegram đã gỡ; người nhận nay định danh bằng email.

Dùng drop + create thay vì alter từng cột: `delivery_log` rỗng và `subscribers` chỉ
có 1 bản ghi test của Telegram (chat_id không map được sang email nào), nên không có
dữ liệu thật để bảo toàn. downgrade() dựng lại đúng schema 009.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("delivery_log")
    op.drop_table("subscribers")

    op.create_table(
        "subscribers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("unsubscribe_token", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_subscribers_email", "subscribers", ["email"], unique=True)
    op.create_index(
        "ix_subscribers_unsubscribe_token", "subscribers", ["unsubscribe_token"], unique=True
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
        sa.Column(
            "subscriber_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscribers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "insight_id", "subscriber_id", "kind",
            name="uq_delivery_log_insight_subscriber_kind",
        ),
    )
    op.create_index("idx_delivery_log_subscriber", "delivery_log", ["subscriber_id"])


def downgrade() -> None:
    op.drop_index("idx_delivery_log_subscriber", table_name="delivery_log")
    op.drop_table("delivery_log")
    op.drop_index("ix_subscribers_unsubscribe_token", table_name="subscribers")
    op.drop_index("ix_subscribers_email", table_name="subscribers")
    op.drop_table("subscribers")

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
