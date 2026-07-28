"""Repository cho `document_chunks` — tầng xếp hạng mức đoạn của chat.

Đây là chỗ DUY NHẤT chạm DB của tín hiệu đoạn (design D4, phương án B). `ChatService._rank`
nhận `chunk_ranks` như một **tham số** và vẫn là hàm thuần — nhờ vậy RS harness đo được xếp
hạng offline, miễn phí, tất định. Đẩy `ORDER BY embedding <=>` vào giữa `_rank` là mất bộ đo
duy nhất bắt được hồi quy xếp hạng.
"""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk

# Số ĐOẠN lấy về từ SQL trước khi gộp về insight. Đây là **cắt để lấy ứng viên**, KHÔNG phải
# ngưỡng similarity (design D5): tập ứng viên cuối vẫn do `_rank` cắt top-K, nên nó không bao
# giờ rỗng vì "không đoạn nào đủ giống".
#
# 300 đoạn ≈ 56% corpus hiện tại (535 đoạn/179 bài) và gộp lại thường phủ >100 tin khác nhau —
# rộng hơn `chat_index_top_k` (60) một quãng an toàn. Lấy quá ít thì tin có đoạn khớp hạng
# ~250 mất hẳn số hạng thứ ba và **im lặng** tụt hạng; lấy cả bảng thì mất chính cái lợi của
# việc đẩy lọc thô xuống index HNSW.
DEFAULT_CHUNK_LIMIT = 300


class DocumentChunkRepository:
    """Data access layer cho bảng document_chunks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replace_for_document(
        self,
        raw_document_id: uuid.UUID,
        insight_id: uuid.UUID | None,
        chunks: list[str],
        embeddings: list[list[float] | None],
    ) -> int:
        """Ghi đè toàn bộ đoạn của một bài. Trả số đoạn đã ghi.

        **Xoá-rồi-ghi chứ không upsert**: số đoạn của một bài thay đổi khi hằng số chunk đổi,
        nên upsert theo `(raw_document_id, ordinal)` sẽ để lại đuôi đoạn cũ của lần chunk
        trước — những hàng mang vector của một họ khác, cạnh tranh xếp hạng bình thường, và
        **không có gì báo lỗi**. Đây cũng là thứ làm hàm này idempotent.
        """
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.raw_document_id == raw_document_id)
        )
        rows = [
            DocumentChunk(
                raw_document_id=raw_document_id,
                insight_id=insight_id,
                ordinal=ordinal,
                content=content,
                # `None` (embed lỗi) giữ nguyên: đoạn vẫn được lưu để backfill vá sau, và
                # truy vấn xếp hạng lọc `embedding IS NOT NULL` nên nó không nhiễu.
                embedding=embedding,
            )
            for ordinal, (content, embedding) in enumerate(zip(chunks, embeddings))
        ]
        self.session.add_all(rows)
        await self.session.commit()
        return len(rows)

    async def retrieve_chunk_ranks(
        self, query_vector: list[float] | None, limit: int = DEFAULT_CHUNK_LIMIT
    ) -> dict[uuid.UUID, int]:
        """`insight_id → thứ hạng của ĐOẠN KHỚP TỐT NHẤT` (design D1).

        Gộp bằng **min** chứ không trung bình: trung bình phạt bài dài vì những đoạn lạc đề
        mà chính nó không chọn có — đúng loại thiên lệch ngầm mà `_vector_ranks` đã phải
        tránh với tin thiếu embedding.

        Thứ hạng ở đây là **thứ hạng đoạn 1..N** (thứ tự trả về của SQL), không phải thứ hạng
        insight. RRF chỉ đọc thứ hạng nên hai thang không cần trùng nhau; điều bắt buộc là
        nó đơn điệu theo độ giống, và `ORDER BY` bảo đảm điều đó.

        `query_vector=None` → `{}`, và `_rank` bỏ hẳn số hạng thứ ba (suy giảm êm: thứ tự
        trùng khít bản hai tín hiệu).
        """
        if query_vector is None:
            return {}

        # `<=>` là cosine distance của pgvector — khớp `vector_cosine_ops` của index HNSW và
        # khớp phép đo `_cosine` dùng ở tầng vector mức insight.
        stmt = (
            select(DocumentChunk.insight_id)
            .where(
                DocumentChunk.embedding.isnot(None),
                # Đoạn chưa nối được vào insight (ingest chạy trước analyze) không có tin để
                # gán thứ hạng cho — loại ở SQL để nó không chiếm suất trong `limit`.
                DocumentChunk.insight_id.isnot(None),
            )
            .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()

        best: dict[uuid.UUID, int] = {}
        for rank, insight_id in enumerate(rows, start=1):
            # Hàng đầu tiên của mỗi insight chính là đoạn khớp tốt nhất của nó — danh sách
            # đã sắp theo khoảng cách nên không cần so lại.
            best.setdefault(insight_id, rank)
        return best

    async def document_ids_with_chunks(self) -> set[uuid.UUID]:
        """Tập `raw_document_id` đã có đoạn — để backfill bỏ qua (idempotent)."""
        rows = (
            await self.session.execute(select(DocumentChunk.raw_document_id).distinct())
        ).scalars().all()
        return set(rows)

    async def delete_for_documents(self, raw_document_ids: list[uuid.UUID]) -> int:
        """Xoá đoạn của các bài đã hết hạn lưu trữ.

        Cần một đường xoá TƯỜNG MINH bên cạnh `ON DELETE CASCADE`: `purge_expired` không xoá
        hàng `raw_documents`, nó chỉ **rỗng hoá `normalized_content`**. Cascade không bắn ở
        đó, và nếu quên gọi hàm này thì đoạn sống sót — tức là corpus vector vẫn giữ nguyên
        nội dung mà chính sách lưu trữ vừa yêu cầu xoá.
        """
        if not raw_document_ids:
            return 0
        result = await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.raw_document_id.in_(raw_document_ids))
        )
        return result.rowcount or 0

    async def count(self) -> int:
        return (await self.session.execute(select(func.count(DocumentChunk.id)))).scalar_one()
