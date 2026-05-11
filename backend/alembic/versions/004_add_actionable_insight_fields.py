"""add actionable insight fields (signal, why_it_matters, recommendations, risks, momentum, urgency, vietnam_relevance)

Revision ID: 004
Revises: 003
Create Date: 2026-05-09 09:50:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("insights", sa.Column("signal", sa.Text(), nullable=True))
    op.add_column("insights", sa.Column("why_it_matters", sa.Text(), nullable=True))
    op.add_column(
        "insights",
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "insights",
        sa.Column("risks", postgresql.ARRAY(sa.Text()), nullable=True),
    )
    op.add_column("insights", sa.Column("momentum", sa.String(length=20), nullable=True))
    op.add_column("insights", sa.Column("urgency", sa.String(length=20), nullable=True))
    op.add_column(
        "insights", sa.Column("vietnam_relevance", sa.String(length=20), nullable=True)
    )
    op.create_index("idx_insights_urgency", "insights", ["urgency"])
    op.create_index("idx_insights_momentum", "insights", ["momentum"])
    op.create_index(
        "idx_insights_vietnam_relevance", "insights", ["vietnam_relevance"]
    )


def downgrade() -> None:
    op.drop_index("idx_insights_vietnam_relevance", table_name="insights")
    op.drop_index("idx_insights_momentum", table_name="insights")
    op.drop_index("idx_insights_urgency", table_name="insights")
    op.drop_column("insights", "vietnam_relevance")
    op.drop_column("insights", "urgency")
    op.drop_column("insights", "momentum")
    op.drop_column("insights", "risks")
    op.drop_column("insights", "recommendations")
    op.drop_column("insights", "why_it_matters")
    op.drop_column("insights", "signal")
