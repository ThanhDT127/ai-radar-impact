"""Repository for RawDocument DB operations."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_document import RawDocument


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

    async def update_status(self, doc_id: uuid.UUID, status: str) -> None:
        """Update processing_status of a raw document."""
        doc = await self.session.get(RawDocument, doc_id)
        if doc:
            doc.processing_status = status
            await self.session.flush()
