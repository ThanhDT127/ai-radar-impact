"""add chat_logs.thinking_tokens (chat-latency-thinking-budget)

Revision ID: 013
Revises: 012
Create Date: 2026-07-27 09:00:00.000000

Số token SUY LUẬN mỗi lượt trả lời chat. Cột này tồn tại vì chi phí đó **ẩn được suốt 5 ngày**:
`google-genai==0.8.0` luôn trả `thoughts_token_count` rỗng, nên nhìn vào `usage_metadata` thì
tưởng thinking = 0 trong khi thực tế nó ăn 1.877–2.752 token/câu và chiếm ~90% độ trễ.

`chat_logs` vốn đã là counter chi phí (`SUM(model_calls)` theo ngày UTC) nên đây là chỗ đúng
để số này sống — thinking bị tính tiền **như output** ($2,50/1M).

**Nullable có chủ đích**: `NULL` = nhà cung cấp không báo cáo, KHÁC hẳn `0` = đã ghìm về 0 và
model tuân thủ. Gộp hai nghĩa vào `0` là xoá mất khả năng phát hiện SDK lại giấu số này.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_logs", sa.Column("thinking_tokens", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_logs", "thinking_tokens")
