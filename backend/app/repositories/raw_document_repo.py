"""Repository for RawDocument DB operations."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_document import RawDocument

# Trạng thái terminal của phân tích — mỗi doc chạm vào đều đã tốn Gemini call.
# 'expired' KHÔNG nằm đây (do purge đặt, không tính vào cap).
TERMINAL_STATUSES = {"analyzed", "low_signal", "failed"}


class RawDocumentRepository:
    """Data access layer for raw_documents table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists_by_fingerprint(self, fingerprint: str) -> bool:
        """Return True if a document with this fingerprint already exists."""
        result = await self.session.execute(
            select(RawDocument.id).where(RawDocument.fingerprint == fingerprint).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        source_id: uuid.UUID,
        source_url: str,
        title: str | None,
        raw_content: str | None,
        normalized_content: str | None,
        author: str | None,
        published_at: datetime | None,
        fingerprint: str,
    ) -> RawDocument:
        """Insert a new raw document and return it."""
        doc = RawDocument(
            source_id=source_id,
            source_url=source_url,
            title=title,
            raw_content=raw_content,
            normalized_content=normalized_content,
            author=author,
            published_at=published_at,
            fingerprint=fingerprint,
            processing_status="pending",
        )
        self.session.add(doc)
        await self.session.flush()  # get auto-generated id without committing
        return doc

    async def get_pending(self, limit: int = 50) -> list[RawDocument]:
        """Return raw documents with processing_status='pending'.

        Ưu tiên tin mới xuất bản trước (published_at DESC) để tin mới lên trang
        trước và không lãng phí quota Gemini vào backlog cũ. Tin không có ngày
        xuất bản (GitHub/HuggingFace) đẩy xuống cuối hàng đợi.
        """
        result = await self.session.execute(
            select(RawDocument)
            .where(RawDocument.processing_status == "pending")
            .order_by(RawDocument.published_at.desc().nulls_last())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_gate_skipped(self, doc_id: uuid.UUID) -> None:
        """Đánh dấu doc đi vào deep analysis mà chưa qua gate (fail-open do gate lỗi).

        Thống kê tỉ lệ qua gate phải lọc `gate_skipped == False`, nếu không doc này
        bị đếm như "qua gate thật".
        """
        doc = await self.session.get(RawDocument, doc_id)
        if doc:
            doc.gate_skipped = True
            await self.session.flush()

    async def update_status(self, doc_id: uuid.UUID, status: str) -> None:
        """Update processing_status of a raw document.

        Khi chuyển sang trạng thái terminal (đã gọi Gemini), stamp `analyzed_at`
        = now để đếm daily cap. Luôn cập nhật (kể cả re-analyze sau reset_failed)
        để lần xử lý được tính vào đúng ngày.
        """
        doc = await self.session.get(RawDocument, doc_id)
        if doc:
            doc.processing_status = status
            if status in TERMINAL_STATUSES:
                doc.analyzed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.session.flush()

    async def count_analyzed_today(self) -> int:
        """Số tài liệu đã gọi Gemini trong ngày hôm nay (UTC) — dùng cho daily cap.

        Đếm theo `analyzed_at` persist trong DB nên đúng xuyên nhiều tiến trình.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
        result = await self.session.execute(
            select(func.count())
            .select_from(RawDocument)
            .where(RawDocument.analyzed_at >= start, RawDocument.analyzed_at < end)
        )
        return int(result.scalar_one())

    async def tombstone_older_than(self, cutoff: datetime) -> int:
        """Tombstone-purge tài liệu có published_at < cutoff.

        Xóa content nặng (raw/normalized) để nhẹ DB nhưng GIỮ `fingerprint` làm
        sổ "đã xử lý" → crawl lại về sau vẫn bị dedup skip, KHÔNG phân tích lại.
        Không hard-delete. Trả về số hàng bị ảnh hưởng.
        """
        result = await self.session.execute(
            update(RawDocument)
            .where(
                RawDocument.published_at < cutoff,
                RawDocument.processing_status != "expired",
            )
            .values(
                processing_status="expired",
                raw_content=None,
                normalized_content=None,
            )
        )
        return result.rowcount or 0
