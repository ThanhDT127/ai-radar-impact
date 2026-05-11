"""add region and target_roles to sources

Revision ID: 005
Revises: 004
Create Date: 2026-05-09 17:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column(
            "region",
            sa.String(length=20),
            nullable=False,
            server_default="global",
        ),
    )
    op.add_column(
        "sources",
        sa.Column(
            "target_roles",
            sa.ARRAY(sa.String(length=50)),
            nullable=False,
            server_default="{}",
        ),
    )
    op.create_index("idx_sources_region", "sources", ["region"])

    # Backfill region for known Vietnamese source
    op.execute("UPDATE sources SET region = 'vietnam' WHERE name = 'VnExpress Số hóa'")

    # Backfill target_roles best-effort by topic (ARRAY values must use ARRAY[]::varchar[])
    op.execute("""
        UPDATE sources SET target_roles = ARRAY['Engineering','Data/AI']::varchar[]
        WHERE source_type = 'rss'
          AND ('Trí tuệ nhân tạo' = ANY(topics) OR 'AI' = ANY(topics))
    """)
    op.execute("""
        UPDATE sources SET target_roles = ARRAY['Engineering','DevOps']::varchar[]
        WHERE name IN ('GitHub Changelog', 'Cloudflare Blog')
    """)
    op.execute("""
        UPDATE sources SET target_roles = ARRAY['Engineering','Infrastructure','DevOps']::varchar[]
        WHERE name = 'AWS What''s New'
    """)
    op.execute("""
        UPDATE sources SET target_roles = ARRAY['Engineering','Toàn công ty']::varchar[]
        WHERE name IN ('Ars Technica', 'IEEE Spectrum', 'HackerNews', 'VnExpress Số hóa')
    """)


def downgrade() -> None:
    op.drop_index("idx_sources_region", table_name="sources")
    op.drop_column("sources", "target_roles")
    op.drop_column("sources", "region")
