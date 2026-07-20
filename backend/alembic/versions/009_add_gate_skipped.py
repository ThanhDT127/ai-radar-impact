"""add gate_skipped to raw_documents (đánh dấu fail-open của gate)

Revision ID: 009
Revises: 008
Create Date: 2026-07-20 15:30:00.000000

Doc bị lỗi parse ở gate được cho đi thẳng vào deep analysis (fail-open) nhưng
trước đây trông y hệt doc qua gate thật, làm sai lệch tỉ lệ qua gate. Cột này
tách hai nhóm đó ra.

KHÔNG backfill: doc cũ mang `false`, tức bị coi như "qua gate thật" — sai với
các doc đã fail-open trước 2026-07-20, nhưng không truy ngược được (design D3).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "raw_documents",
        sa.Column(
            "gate_skipped",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("raw_documents", "gate_skipped")
