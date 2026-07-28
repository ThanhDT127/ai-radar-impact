"""Tombstone-purge insights/raw_documents quá hạn retention (W1 quota guard).

Quá `retention_months` (mặc định 6): ẩn insight (status='expired'), xóa content
nặng của raw_document nhưng GIỮ `fingerprint` → crawl lại về sau vẫn bị dedup
skip, KHÔNG phân tích lại → không tốn quota Gemini. KHÔNG hard-delete.

Usage:
    docker-compose exec backend python -m app.scripts.purge_expired
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.repositories.document_chunk_repo import DocumentChunkRepository
from app.repositories.insight_repo import InsightRepository
from app.repositories.raw_document_repo import RawDocumentRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Xấp xỉ 1 tháng = 30 ngày (khớp freshness gate trong ingestion).
DAYS_PER_MONTH = 30


async def purge_expired(session: AsyncSession) -> dict[str, int]:
    """Chạy tombstone-purge trong 1 session. Trả về counts."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=settings.retention_months * DAYS_PER_MONTH)

    # Ẩn insight trước (khớp thứ tự spec; soft-purge nên FK không ảnh hưởng).
    insights_expired = await InsightRepository(session).expire_older_than(cutoff)

    raw_doc_repo = RawDocumentRepository(session)
    # ⚠️ Phải hỏi id TRƯỚC khi tombstone — sau lượt update thì vị từ này trả rỗng.
    #
    # Và phải xoá đoạn TƯỜNG MINH: `document_chunks` có `ON DELETE CASCADE`, nhưng purge
    # KHÔNG xoá hàng `raw_documents`, nó chỉ rỗng hoá `normalized_content`. Cascade không
    # bắn, nên bỏ bước này thì corpus vector vẫn giữ nguyên nội dung mà chính sách lưu trữ
    # vừa yêu cầu xoá — và giữ nó ở dạng đọc lại được (`document_chunks.content`).
    expiring_doc_ids = await raw_doc_repo.ids_older_than(cutoff)
    chunks_deleted = await DocumentChunkRepository(session).delete_for_documents(
        expiring_doc_ids
    )
    docs_tombstoned = await raw_doc_repo.tombstone_older_than(cutoff)
    await session.commit()

    counts = {
        "insights_expired": insights_expired,
        "docs_tombstoned": docs_tombstoned,
        "chunks_deleted": chunks_deleted,
    }
    logger.info(
        "Purge complete (cutoff=%s) — insights expired: %d, docs tombstoned: %d, "
        "chunks deleted: %d",
        cutoff.date(), insights_expired, docs_tombstoned, chunks_deleted,
    )
    return counts


async def main() -> None:
    async with async_session_maker() as session:
        await purge_expired(session)


if __name__ == "__main__":
    asyncio.run(main())
