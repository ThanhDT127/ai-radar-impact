"""add analyzed_at to raw_documents + lifecycle backfill (W1 quota guard)

Revision ID: 007
Revises: 006
Create Date: 2026-07-07 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cột đếm cap theo ngày: set khi doc đạt trạng thái terminal (analyzed/low_signal/failed)
    op.add_column(
        "raw_documents",
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "idx_raw_documents_analyzed_at", "raw_documents", ["analyzed_at"]
    )

    # Backfill 1: doc thiếu ngày xuất bản → dùng ngày crawl (fetched_at)
    # để không kẹt cuối hàng đợi và luôn "trong vòng" freshness gate.
    op.execute(
        "UPDATE raw_documents SET published_at = fetched_at WHERE published_at IS NULL"
    )

    # Backfill 2: doc đã ở trạng thái terminal → khởi tạo analyzed_at = updated_at.
    # (updated_at cũ ⇒ cap của hôm nay bắt đầu ~0, không chặn nhầm.)
    op.execute(
        "UPDATE raw_documents SET analyzed_at = updated_at "
        "WHERE analyzed_at IS NULL "
        "AND processing_status IN ('analyzed', 'low_signal', 'failed')"
    )


def downgrade() -> None:
    op.drop_index("idx_raw_documents_analyzed_at", table_name="raw_documents")
    op.drop_column("raw_documents", "analyzed_at")
