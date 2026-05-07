"""RSS connector — fetches entries from an RSS/Atom feed using feedparser."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser

from app.models.source import Source

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 500
MAX_AUTHOR_LENGTH = 255


@dataclass
class FeedEntry:
    """Normalized RSS entry ready for further processing."""

    source_url: str
    title: str
    raw_content: str
    author: str | None
    published_at: datetime | None


class RSSConnector:
    """Fetches entries from an RSS/Atom feed."""

    def fetch(self, source: Source) -> list[FeedEntry]:
        """Fetch and normalize entries from the source feed URL.

        Returns a list of FeedEntry objects.
        Logs and returns empty list on any error.
        """
        if not source.feed_url:
            logger.warning("Source %s has no feed_url — skipping", source.name)
            return []

        max_items: int = source.config.get("max_items", 20) if source.config else 20

        try:
            feed = feedparser.parse(source.feed_url)
        except Exception as e:
            logger.error("Failed to parse feed %s: %s", source.feed_url, e)
            return []

        if feed.bozo and feed.bozo_exception:
            logger.warning(
                "Feed %s parsed with errors: %s", source.feed_url, feed.bozo_exception
            )

        entries: list[FeedEntry] = []
        for entry in feed.entries[:max_items]:
            try:
                entries.append(self._normalize_entry(entry))
            except Exception as e:
                logger.warning("Could not normalize entry from %s: %s", source.feed_url, e)

        logger.info("Fetched %d entries from %s", len(entries), source.feed_url)
        return entries

    def _normalize_entry(self, entry: feedparser.FeedParserDict) -> FeedEntry:
        """Convert a feedparser entry into a FeedEntry."""
        # URL
        source_url: str = entry.get("link", "") or ""

        # Title
        title: str = (entry.get("title", "") or "Untitled")[:MAX_TITLE_LENGTH]

        # Content: prefer content[0].value, then summary
        raw_content = ""
        if entry.get("content"):
            raw_content = entry["content"][0].get("value", "") or ""
        if not raw_content:
            raw_content = entry.get("summary", "") or ""

        # Author
        author_raw = entry.get("author") or None
        author: str | None = author_raw[:MAX_AUTHOR_LENGTH] if author_raw else None

        # Published date
        published_at: datetime | None = None
        if entry.get("published_parsed"):
            try:
                # Build UTC naive datetime (column is TIMESTAMP WITHOUT TIME ZONE)
                published_at = datetime(*entry["published_parsed"][:6])  # naive UTC
            except Exception:
                pass

        return FeedEntry(
            source_url=source_url,
            title=title,
            raw_content=raw_content,
            author=author,
            published_at=published_at,
        )
