"""Add taxonomy overhaul fields: actionability_score, intelligence_tier, so_what, adoption_ring, practical_indicators.

Revision ID: 006
Revises: 005
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("insights", sa.Column("actionability_score", sa.Float(), nullable=True))
    op.add_column("insights", sa.Column("intelligence_tier", sa.String(20), nullable=True))
    op.add_column("insights", sa.Column("so_what", sa.Text(), nullable=True))
    op.add_column("insights", sa.Column("adoption_ring", sa.String(20), nullable=True))
    op.add_column("insights", sa.Column("practical_indicators", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("insights", "practical_indicators")
    op.drop_column("insights", "adoption_ring")
    op.drop_column("insights", "so_what")
    op.drop_column("insights", "intelligence_tier")
    op.drop_column("insights", "actionability_score")
