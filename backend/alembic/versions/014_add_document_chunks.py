"""add document_chunks + HNSW cosine (chat-chunk-retrieval)

Revision ID: 014
Revises: 013
Create Date: 2026-07-28 07:00:00.000000

Đoạn của `raw_documents.normalized_content` kèm embedding, làm **tín hiệu xếp hạng thứ ba**
của chat (RRF: lexical + vector mức insight + vector mức đoạn). Lý do tồn tại: hai tín hiệu
cũ đều đọc *bản phân tích do Gemini viết*, phủ 4% từ vựng thân bài — hỏi bằng một định danh
chỉ có trong bài (`SquashFS`, `SPDX`, `HMAC-SHA256`) thì không tín hiệu nào biết bài đó tồn
tại. Đo 28/07: recall@5 nhóm "khám phá bằng chi tiết" 0,667 → 1,000.

⚠️ Đoạn **KHÔNG BAO GIỜ** là đích của marker trích dẫn `[n]` — nó chỉ phục vụ xếp hạng
(design "chunk XẾP HẠNG, insight TRÍCH DẪN"). Nội dung đưa vào câu trả lời vẫn đến từ ô sâu
của `chat-context-depth`.

⚠️ KHÔNG gọi Vertex ở đây, cùng luật với migration 012: `alembic upgrade head` phải tất định
và chạy được offline. Backfill là việc của `app.scripts.chunk_documents`.

`insight_id` NULLABLE có chủ đích: đoạn có thể sinh trước khi insight tồn tại (ingest chạy
trước analyze), và nối lại lúc publish.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `vector` đã có từ 012; `IF NOT EXISTS` để migration này đứng vững cả khi ai đó chạy
    # nó trên một database dựng lại từ nhánh khác.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE document_chunks (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            raw_document_id UUID NOT NULL REFERENCES raw_documents(id) ON DELETE CASCADE,
            insight_id      UUID     NULL REFERENCES insights(id)      ON DELETE CASCADE,
            ordinal         INTEGER NOT NULL,
            content         TEXT NOT NULL,
            embedding       vector(768),
            created_at      TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT uq_document_chunks_doc_ordinal UNIQUE (raw_document_id, ordinal)
        )
        """
    )
    # `ON DELETE CASCADE` ở cả hai khoá ngoại là phần CƠ CHẾ của "xoá đoạn cùng lúc xoá nội
    # dung bài gốc": `purge_expired` xoá `raw_documents` thì đoạn đi theo, không cần nhớ.
    # Đường xoá riêng cho ca chỉ rỗng `normalized_content` mà giữ hàng nằm ở script purge.

    # 768 chiều, cosine — CÙNG model và cùng phép đo với `insights.embedding`. Trộn hai họ
    # vector trong hai cột mà so bằng một câu hỏi sẽ cho thứ hạng lệch **không báo lỗi**.
    op.execute(
        "CREATE INDEX idx_document_chunks_embedding_hnsw ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    # Truy vấn thật gộp thứ hạng đoạn về insight, nên `insight_id` là cột lọc/gộp nóng.
    op.execute("CREATE INDEX idx_document_chunks_insight ON document_chunks (insight_id)")


def downgrade() -> None:
    # DROP TABLE bỏ luôn index và constraint của chính bảng đó. Giữ lại extension `vector`
    # vì `insights.embedding` (012) vẫn đang dùng nó.
    op.execute("DROP TABLE IF EXISTS document_chunks")
