"""Analyzer service — runs Gemini analysis on pending raw documents and creates insights."""

import logging
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import ALLOWED_ACTION_TYPES
from app.config import settings
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.repositories.insight_repo import InsightRepository
from app.repositories.raw_document_repo import RawDocumentRepository

logger = logging.getLogger(__name__)

# In-memory daily analysis counter — resets at midnight
_daily_counter: dict[str, int] = {"date": "", "count": 0}


def _get_daily_count() -> int:
    today = str(date.today())
    if _daily_counter["date"] != today:
        _daily_counter["date"] = today
        _daily_counter["count"] = 0
    return _daily_counter["count"]  # type: ignore[return-value]


def _increment_daily_count() -> None:
    _get_daily_count()  # ensure reset if new day
    _daily_counter["count"] = _daily_counter["count"] + 1  # type: ignore[assignment]

# Rule-based trust score mapping from source trust_tier
TRUST_SCORE_MAP: dict[str, float] = {
    "very_high": 0.95,
    "high": 0.80,
    "medium": 0.60,
    "low": 0.40,
    "unverified": 0.20,
}

# Rule-based impact label mapping from event_type (tiếng Việt)
IMPACT_LABEL_MAP: dict[str, str] = {
    "Cảnh báo bảo mật": "Nghiêm trọng",
    "Cập nhật quy định": "Cao",
    "Thay đổi chính sách": "Cao",
    "Ngừng hỗ trợ": "Cao",
    "Phát hành mới": "Trung bình",
    "Sự cố vận hành": "Trung bình",
    "Cập nhật nghiên cứu": "Thấp",
    "Tín hiệu xu hướng": "Thấp",
    "Thảo luận cộng đồng": "Theo dõi",
}

MIN_CONFIDENCE = 0.3  # Below this, do not publish

# Vietnamese-specific topics for vietnam_relevance medium tier
_VN_SPECIFIC_TOPICS = {"Pháp lý/Tuân thủ", "Quản trị nội bộ"}


def _validate_recommendations(
    recs: dict | None, affected_roles: list[str]
) -> dict | None:
    """Drop recommendations whose role ∉ affected_roles or action_type invalid.

    Returns None if no valid entries remain (instead of empty dict for clarity).
    """
    if not isinstance(recs, dict) or not recs:
        return None
    affected = set(affected_roles or [])
    cleaned: dict = {}
    for role, value in recs.items():
        if role not in affected:
            logger.warning(
                "Dropping recommendation for role '%s' (not in affected_roles)", role
            )
            continue
        if not isinstance(value, dict):
            logger.warning("Dropping malformed recommendation for role '%s'", role)
            continue
        action_type = value.get("action_type")
        note = value.get("note")
        if action_type not in ALLOWED_ACTION_TYPES:
            logger.warning(
                "Dropping recommendation for role '%s' (invalid action_type=%r)",
                role,
                action_type,
            )
            continue
        if not isinstance(note, str) or not note.strip():
            continue
        cleaned[role] = {"action_type": action_type, "note": note.strip()}
    return cleaned or None


def _compute_urgency(
    impact_label: str | None, published_at: datetime | None
) -> str:
    """Rule D3: critical/high/medium/low from impact_label + recency."""
    if impact_label is None:
        return "low"

    if published_at is None:
        # No published date — fall back to impact_label only
        if impact_label == "Nghiêm trọng":
            return "critical"
        if impact_label == "Cao":
            return "medium"
        if impact_label == "Trung bình":
            return "medium"
        return "low"

    now = datetime.now(timezone.utc)
    pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    age_days = (now - pub).days
    is_recent = age_days < 14

    if impact_label == "Nghiêm trọng" and is_recent:
        return "critical"
    if impact_label == "Cao" and is_recent:
        return "high"
    if impact_label == "Trung bình":
        return "medium"
    if impact_label == "Cao" and not is_recent:
        return "medium"
    return "low"


def _compute_vietnam_relevance(source: Source, topics: list[str]) -> str:
    """Rule D4: high/medium/low from source.config.language + topics."""
    config = source.config or {}
    language = config.get("language", "")
    topics_set = set(topics or [])

    if language == "vi" or "Pháp lý/Tuân thủ" in topics_set:
        return "high"
    if topics_set & _VN_SPECIFIC_TOPICS:
        return "medium"
    return "low"


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
        impact_label = IMPACT_LABEL_MAP.get(result.event_type or "", "Thấp")

        # v2 actionable fields — graceful: AI fields may be None if Gemini malformed
        recommendations = _validate_recommendations(
            result.recommendations, result.affected_roles
        )
        urgency = _compute_urgency(impact_label, raw_doc.published_at)
        vietnam_relevance = _compute_vietnam_relevance(source, result.topics)

        # Create insight
        await self.insight_repo.create(
            raw_document_id=raw_doc.id,
            title=raw_doc.title or "Chưa có tiêu đề",
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
            affected_roles=result.affected_roles,
            published_at=raw_doc.published_at,
            signal=result.signal,
            why_it_matters=result.why_it_matters,
            recommendations=recommendations,
            risks=result.risks,
            urgency=urgency,
            vietnam_relevance=vietnam_relevance,
        )

        await self.raw_doc_repo.update_status(raw_doc.id, "analyzed")
        return True

    async def run_pending(self, limit: int = 50) -> dict[str, int]:
        """Process up to `limit` pending raw documents, subject to daily cap.

        Returns counts: { created, skipped, errors }.
        """
        daily_used = _get_daily_count()
        daily_remaining = settings.max_daily_analysis - daily_used
        if daily_remaining <= 0:
            logger.warning("Daily analysis cap reached (%d). Skipping.", settings.max_daily_analysis)
            return {"created": 0, "skipped": 0, "errors": 0}

        effective_limit = min(limit, daily_remaining)
        pending = await self.raw_doc_repo.get_pending(limit=effective_limit)
        logger.info("Analyzing %d pending documents (daily cap: %d used / %d)", len(pending), daily_used, settings.max_daily_analysis)

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
                    _increment_daily_count()
                else:
                    counts["skipped"] += 1
            except Exception as e:
                logger.error("Unexpected error analyzing doc %s: %s", raw_doc.id, e)
                counts["errors"] += 1

        await self.session.commit()
        logger.info("Analysis complete — %s", counts)

        if counts["created"] > 0:
            from app.services.dedup_engine import DeduplicationEngine
            dedup = DeduplicationEngine(self.session)
            dedup_result = await dedup.run_dedup()
            counts["clusters_created"] = dedup_result["clusters_created"]
            counts["duplicates_marked"] = dedup_result["duplicates_marked"]

        return counts
