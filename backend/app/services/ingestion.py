"""Ingestion service — orchestrates fetch → normalize → dedup → store → analyze pipeline."""

import asyncio
import logging
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.connectors import ConnectorRegistry
from app.connectors.base import ConnectorEntry
from app.repositories.raw_document_repo import RawDocumentRepository
from app.repositories.source_repo import SourceRepository
from app.services.normalizer import normalize_entry

logger = logging.getLogger(__name__)

# Xấp xỉ 1 tháng = 30 ngày cho freshness gate / retention.
DAYS_PER_MONTH = 30


def _to_naive_utc(dt: datetime | None) -> datetime | None:
    """Coerce datetime về naive UTC để so sánh với cột DateTime (không tz)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def _fetch_with_retry(connector, source) -> list[ConnectorEntry]:
    """Gọi connector.fetch với exponential backoff khi lỗi (vd 429/403).

    Lùi thời gian thử lại thay vì fetch dồn dập → giảm nguy cơ bị chặn.
    """
    last_exc: Exception | None = None
    for attempt in range(1, settings.fetch_max_retries + 1):
        try:
            return connector.fetch(source)
        except Exception as e:  # noqa: BLE001 — mọi lỗi fetch đều retry rồi mới raise
            last_exc = e
            if attempt < settings.fetch_max_retries:
                backoff = settings.fetch_backoff_base_seconds * (2 ** (attempt - 1))
                backoff += random.uniform(0, settings.ingest_jitter_seconds)
                logger.warning(
                    "Fetch '%s' lỗi (lần %d/%d): %s — backoff %.1fs",
                    source.name, attempt, settings.fetch_max_retries, e, backoff,
                )
                await asyncio.sleep(backoff)
    assert last_exc is not None
    raise last_exc


@dataclass
class IngestionSummary:
    """Result summary from one ingestion run."""

    new: int = 0
    skipped: int = 0
    skipped_old: int = 0
    errors: int = 0
    insights_created: int = 0


class IngestionService:
    """Coordinates the full ingestion pipeline for one or all sources."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.raw_doc_repo = RawDocumentRepository(session)

    async def run(self, source_id: uuid.UUID | None = None) -> IngestionSummary:
        """Run ingestion for all active sources, or a single source by ID.

        Returns an IngestionSummary with counts.
        """
        summary = IngestionSummary()

        # Get sources
        if source_id:
            source = await self.source_repo.get_by_id(source_id)
            sources = [source] if source else []
        else:
            sources = await self.source_repo.get_active_sources()

        if not sources:
            logger.warning("No active sources found.")
            return summary

        for idx, source in enumerate(sources):
            # Rate-limit: giãn request giữa các nguồn (jitter) để tránh 429/403.
            if idx > 0:
                delay = settings.ingest_source_delay_seconds + random.uniform(
                    0, settings.ingest_jitter_seconds
                )
                await asyncio.sleep(delay)

            logger.info("Ingesting source: %s (%s)", source.name, source.source_type)

            # Fetch entries via registry (retry + backoff khi lỗi)
            try:
                connector = ConnectorRegistry.get(source.source_type)
            except ValueError:
                logger.warning("No connector registered for source_type '%s' — skipping", source.source_type)
                continue
            try:
                entries = await _fetch_with_retry(connector, source)
            except Exception as e:
                logger.error("Error fetching source %s: %s", source.name, e)
                summary.errors += 1
                continue

            # Process each entry
            for entry in entries:
                try:
                    normalized_content, fingerprint = normalize_entry(entry)

                    # Min content length filter
                    min_len = (
                        source.config.get("min_content_length", settings.min_content_length)
                        if source.config
                        else settings.min_content_length
                    )
                    if len(normalized_content) < min_len:
                        logger.debug("Skipping short content (%d chars) from '%s'", len(normalized_content), entry.title[:60])
                        summary.skipped += 1
                        continue

                    # Crawl-date fallback: doc thiếu ngày (GitHub/HF...) lấy ngày crawl
                    # để không kẹt cuối hàng đợi và luôn nằm trong freshness window.
                    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                    published_at = _to_naive_utc(entry.published_at) or now_naive

                    # Freshness gate: bỏ qua bài cũ hơn max_age_months (0 chi phí Gemini).
                    max_age_months = (
                        source.config.get("max_age_months", settings.max_age_months)
                        if source.config
                        else settings.max_age_months
                    )
                    cutoff = now_naive - timedelta(days=max_age_months * DAYS_PER_MONTH)
                    if published_at < cutoff:
                        logger.debug(
                            "Skipping stale content (published %s < %s) from '%s'",
                            published_at.date(), cutoff.date(), entry.title[:60],
                        )
                        summary.skipped_old += 1
                        continue

                    # Dedup check
                    if await self.raw_doc_repo.exists_by_fingerprint(fingerprint):
                        summary.skipped += 1
                        continue

                    # Store raw document
                    await self.raw_doc_repo.create(
                        source_id=source.id,
                        source_url=entry.source_url,
                        title=entry.title,
                        raw_content=entry.raw_content,
                        normalized_content=normalized_content,
                        author=entry.author,
                        published_at=published_at,
                        fingerprint=fingerprint,
                    )
                    await self.session.commit()
                    summary.new += 1

                except Exception as e:
                    logger.error("Error processing entry '%s': %s", entry.title, e)
                    await self.session.rollback()
                    summary.errors += 1

        # Run AI analysis on newly added documents
        if summary.new > 0:
            from app.services.analyzer import AnalyzerService
            analyzer = AnalyzerService(self.session)
            analysis_counts = await analyzer.run_pending()
            summary.insights_created = analysis_counts.get("created", 0)

        logger.info(
            "Ingestion complete — new: %d, skipped: %d, skipped_old: %d, errors: %d, insights: %d",
            summary.new, summary.skipped, summary.skipped_old, summary.errors, summary.insights_created,
        )
        return summary
