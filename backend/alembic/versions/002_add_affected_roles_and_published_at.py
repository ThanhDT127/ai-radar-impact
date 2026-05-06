"""add affected_roles and published_at to insights

Revision ID: 002
Revises: 001
Create Date: 2026-05-06 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add affected_roles: array of role strings (nullable, default empty array)
    op.add_column(
        "insights",
        sa.Column(
            "affected_roles",
            postgresql.ARRAY(sa.String()),
            nullable=True,
            server_default="{}",
        ),
    )

    # Add published_at: original publish date from source document (nullable)
    op.add_column(
        "insights",
        sa.Column("published_at", sa.TIMESTAMP(), nullable=True),
    )

    # Widen event_type from String(50) to String(80) for Vietnamese labels
    op.alter_column(
        "insights",
        "event_type",
        existing_type=sa.String(50),
        type_=sa.String(80),
        existing_nullable=True,
    )

    # Widen impact_label from String(20) to String(30) for Vietnamese labels
    op.alter_column(
        "insights",
        "impact_label",
        existing_type=sa.String(20),
        type_=sa.String(30),
        existing_nullable=True,
    )

    # Index for role filtering (GIN index for ARRAY queries)
    op.create_index(
        "idx_insights_affected_roles",
        "insights",
        ["affected_roles"],
        postgresql_using="gin",
    )

    # Index for published_at sorting
    op.create_index(
        "idx_insights_published_at",
        "insights",
        ["published_at"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("idx_insights_published_at", table_name="insights")
    op.drop_index("idx_insights_affected_roles", table_name="insights")
    op.alter_column(
        "insights",
        "impact_label",
        existing_type=sa.String(30),
        type_=sa.String(20),
        existing_nullable=True,
    )
    op.alter_column(
        "insights",
        "event_type",
        existing_type=sa.String(80),
        type_=sa.String(50),
        existing_nullable=True,
    )
    op.drop_column("insights", "published_at")
    op.drop_column("insights", "affected_roles")
