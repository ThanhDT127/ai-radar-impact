"""Analyzer service — runs Gemini analysis on pending raw documents and creates insights."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import GeminiClient
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.repositories.insight_repo import InsightRepository
from app.repositories.raw_document_repo import RawDocumentRepository

logger = logging.getLogger(__name__)

# Rule-based trust score mapping from source trust_tier
TRUST_SCORE_MAP: dict[str, float] = {
    "very_high": 0.95,
    "high": 0.80,
    "medium": 0.60,
    "low": 0.40,
    "unverified": 0.20,
}

# Rule-based impact label mapping from event_type
IMPACT_LABEL_MAP: dict[str, str] = {
    "Security alert": "High",
    "Deprecation": "High",
    "Policy change": "High",
    "Regulation update": "High",
    "New release": "Medium",
    "Operational incident": "Medium",
    "Research update": "Low",
    "Trend signal": "Low",
    "Community discussion": "Watch",
}

MIN_CONFIDENCE = 0.3  # Below this, do not publish


class AnalyzerService:
    """Analyzes pending raw documents using Gemini and creates insights."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.raw_doc_repo = RawDocumentRepository(session)
        self.insight_repo = InsightRepository(session)
        self.gemini = GeminiClient()

    async def analyze_document(self, raw_doc: RawDocument, source: Source) -> bool:
        """Analyze a single raw document and create an insight.

        Returns True if insight was created, False otherwise.
        """
        content = raw_doc.normalized_content or raw_doc.raw_content or ""
        if not content.strip():
            logger.warning("Skipping document %s — no content", raw_doc.id)
            await self.raw_doc_repo.update_status(raw_doc.id, "failed")
            return False

        # Call Gemini
        result = self.gemini.analyze(title=raw_doc.title or "", content=content)

        if result.error:
            logger.error("Analysis failed for doc %s: %s", raw_doc.id, result.error)
            await self.raw_doc_repo.update_status(raw_doc.id, "failed")
            return False

        if result.confidence < MIN_CONFIDENCE:
            logger.warning(
                "Low confidence (%.2f) for doc %s — skipping insight", result.confidence, raw_doc.id
            )
            await self.raw_doc_repo.update_status(raw_doc.id, "failed")
            return False

        # Rule-based scoring
        trust_score = TRUST_SCORE_MAP.get(source.trust_tier, 0.5)
        impact_label = IMPACT_LABEL_MAP.get(result.event_type or "", "Low")

        # Create insight
        await self.insight_repo.create(
            raw_document_id=raw_doc.id,
            title=raw_doc.title or "Untitled",
            summary_short=result.summary_short,
            summary_medium=result.summary_medium,
            topics=result.topics,
            event_type=result.event_type,
            nature=result.nature,
            trust_score=trust_score,
            impact_label=impact_label,
            source_url=raw_doc.source_url,
            confidence=result.confidence,
            ai_raw_response=result.raw_response,
        )

        await self.raw_doc_repo.update_status(raw_doc.id, "analyzed")
        return True

    async def run_pending(self, limit: int = 50) -> dict[str, int]:
        """Process up to `limit` pending raw documents.

        Returns counts: { created, skipped, errors }.
        """
        pending = await self.raw_doc_repo.get_pending(limit=limit)
        logger.info("Analyzing %d pending documents", len(pending))

        counts = {"created": 0, "skipped": 0, "errors": 0}

        for raw_doc in pending:
            # Explicitly load source via async query (lazy relationship is not safe in async)
            from app.repositories.source_repo import SourceRepository
            source = await SourceRepository(self.session).get_by_id(raw_doc.source_id)

            if source is None:
                logger.error("No source found for doc %s", raw_doc.id)
                counts["errors"] += 1
                continue

            try:
                created = await self.analyze_document(raw_doc, source)
                if created:
                    counts["created"] += 1
                else:
                    counts["skipped"] += 1
            except Exception as e:
                logger.error("Unexpected error analyzing doc %s: %s", raw_doc.id, e)
                counts["errors"] += 1

        await self.session.commit()
        logger.info("Analysis complete — %s", counts)
        return counts
