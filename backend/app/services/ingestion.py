"""Ingestion service — orchestrates fetch → normalize → dedup → store → analyze pipeline."""

import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.connectors import ConnectorRegistry
from app.repositories.raw_document_repo import RawDocumentRepository
from app.repositories.source_repo import SourceRepository
from app.services.normalizer import normalize_entry

logger = logging.getLogger(__name__)


@dataclass
class IngestionSummary:
    """Result summary from one ingestion run."""

    new: int = 0
    skipped: int = 0
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

        for source in sources:
            logger.info("Ingesting source: %s (%s)", source.name, source.source_type)

            # Fetch entries via registry
            try:
                connector = ConnectorRegistry.get(source.source_type)
                entries = connector.fetch(source)
            except ValueError:
                logger.warning("No connector registered for source_type '%s' — skipping", source.source_type)
                continue
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
                        published_at=entry.published_at,
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
            "Ingestion complete — new: %d, skipped: %d, errors: %d, insights: %d",
            summary.new, summary.skipped, summary.errors, summary.insights_created,
        )
        return summary
