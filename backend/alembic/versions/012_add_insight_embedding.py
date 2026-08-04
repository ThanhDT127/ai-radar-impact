"""add insights.embedding vector(768) + pgvector (chat-hybrid-retrieval)

Revision ID: 012
Revises: 011
Create Date: 2026-07-27 07:00:00.000000

Cột embedding cho xếp hạng lai của chat (RRF vector + lexical). **Nullable có chủ đích**:
tin chưa embed vẫn phải tham gia xếp hạng qua tầng lexical (design D6), nên NULL là trạng
thái hợp lệ chứ không phải dữ liệu hỏng.

⚠️ Migration này KHÔNG gọi Vertex (design D4). Migration phải tất định và chạy được offline;
một `alembic upgrade head` mà lại phụ thuộc credentials + mạng + hạn mức API là thứ sẽ hỏng
đúng lúc dựng lại môi trường. Backfill là việc của `app.scripts.embed_insights`.

⚠️ Cần image Postgres CÓ pgvector (`pgvector/pgvector:pg16`). `postgres:16` trần không có
extension `vector` và bước `CREATE EXTENSION` dưới đây sẽ đỏ ngay.

768 chiều chốt cứng theo `text-multilingual-embedding-002` (design D1) — đổi chiều sau là
đổi schema, nên xác minh đã làm TRƯỚC khi viết migration này.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # SQL thuần cho cột `vector`: kiểu này do extension định nghĩa, không có trong `sa.types`.
    # Dùng SQL trực tiếp cũng giữ migration độc lập với package `pgvector` phía Python — nó
    # chỉ cần cho ORM, không nên là điều kiện để `alembic upgrade head` chạy được.
    op.execute("ALTER TABLE insights ADD COLUMN embedding vector(768)")
    # HNSW chứ không IVFFlat (Open Question chốt 27/07): pgvector 0.8.5 trong image có sẵn
    # cả hai, HNSW recall tốt hơn và KHÔNG cần dữ liệu mồi để dựng danh sách (IVFFlat dựng
    # index trên bảng rỗng/gần rỗng cho recall tệ cho tới khi REINDEX).
    #
    # `vector_cosine_ops` khớp phép đo dùng ở tầng xếp hạng. Index này hiện chỉ là hạ tầng
    # dự phòng: `_rank` tính cosine trong Python trên tập ứng viên đã nạp sẵn (giữ `_rank`
    # thuần để RS harness đo được offline). Nó có ích khi corpus lớn tới mức phải lọc ngay
    # trong SQL — dựng sẵn ở đây vì lúc đó thêm index vào bảng lớn mới là việc tốn kém.
    op.execute(
        "CREATE INDEX idx_insights_embedding_hnsw ON insights "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_insights_embedding_hnsw")
    op.drop_column("insights", "embedding")
    # KHÔNG `DROP EXTENSION vector`: extension là tài nguyên cấp database, có thể đã được
    # thứ khác dùng, và bỏ lại nó hoàn toàn vô hại. Downgrade phải trả lại schema của
    # BẢNG, không phải dọn sạch cả database.
