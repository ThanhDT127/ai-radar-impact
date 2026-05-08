"""add cluster_id and is_primary to insights

Revision ID: 003
Revises: 002
Create Date: 2026-05-08 15:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "insights",
        sa.Column(
            "cluster_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "insights",
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_index(
        "idx_insights_cluster_id",
        "insights",
        ["cluster_id"],
        postgresql_where=sa.text("cluster_id IS NOT NULL"),
    )
    op.create_index(
        "idx_insights_is_primary",
        "insights",
        ["is_primary"],
    )


def downgrade() -> None:
    op.drop_index("idx_insights_is_primary", table_name="insights")
    op.drop_index("idx_insights_cluster_id", table_name="insights")
    op.drop_column("insights", "is_primary")
    op.drop_column("insights", "cluster_id")
