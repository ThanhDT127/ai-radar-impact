"""add chat_logs.web_searches (chat-web-fallback)

Revision ID: 015
Revises: 014
Create Date: 2026-08-03 10:00:00.000000

Số TRUY VẤN tra cứu ngoài của một lượt chat.

Cột này tồn tại vì `max_daily_web_searches` là một trần **tiền**, và trần tiền phải sống sót
qua restart. Bộ đếm trong bộ nhớ sẽ reset mỗi lần tiến trình khởi động lại — một vòng lặp
restart là một vòng lặp tiêu tiền không giới hạn. `chat_logs` vốn đã là counter budget
(`SUM(model_calls)` theo ngày UTC), nên đây là chỗ đúng, cùng khuôn với migration 013.

Vì sao KHÔNG gộp vào `model_calls`: hai đơn giá cách nhau bậc. Grounding with Google Search
là **$35/1.000 truy vấn** (Gemini 2.x, đo 03/08/2026) trong khi cả một câu trả lời ~19k token
tốn ~$0,006 — tức một lần tra cứu ≈ 6× toàn bộ câu trả lời. Trộn chung một bộ đếm là để loại
rẻ bào mòn budget của loại đắt, đúng cái bẫy "đơn vị budget khác nhau" đã ghi trong CLAUDE.md.

**Nullable có chủ đích**, cùng lý do với 013: `NULL` = bản ghi có trước change này (không biết),
`0` = lượt đó thật sự không tra cứu. Gộp hai nghĩa là xoá mất khả năng đọc lại lịch sử.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_logs", sa.Column("web_searches", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_logs", "web_searches")
