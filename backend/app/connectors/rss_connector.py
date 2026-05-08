"""RSS connector — fetches entries from an RSS/Atom feed using feedparser."""

import logging
from datetime import datetime

import feedparser

from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.models.source import Source

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 500
MAX_AUTHOR_LENGTH = 255


class RSSConnector(BaseConnector):
    """Fetches entries from an RSS/Atom feed."""

    def fetch(self, source: Source) -> list[ConnectorEntry]:
        """Fetch and normalize entries from the source feed URL.

        Returns a list of ConnectorEntry objects.
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

        entries: list[ConnectorEntry] = []
        for entry in feed.entries[:max_items]:
            try:
                entries.append(self._normalize_entry(entry))
            except Exception as e:
                logger.warning("Could not normalize entry from %s: %s", source.feed_url, e)

        logger.info("Fetched %d entries from %s", len(entries), source.feed_url)
        return entries

    def _normalize_entry(self, entry: feedparser.FeedParserDict) -> ConnectorEntry:
        """Convert a feedparser entry into a ConnectorEntry."""
        source_url: str = entry.get("link", "") or ""
        title: str = (entry.get("title", "") or "Untitled")[:MAX_TITLE_LENGTH]

        raw_content = ""
        if entry.get("content"):
            raw_content = entry["content"][0].get("value", "") or ""
        if not raw_content:
            raw_content = entry.get("summary", "") or ""

        author_raw = entry.get("author") or None
        author: str | None = author_raw[:MAX_AUTHOR_LENGTH] if author_raw else None

        published_at: datetime | None = None
        if entry.get("published_parsed"):
            try:
                published_at = datetime(*entry["published_parsed"][:6])
            except Exception:
                pass

        return ConnectorEntry(
            source_url=source_url,
            title=title,
            raw_content=raw_content,
            author=author,
            published_at=published_at,
        )


ConnectorRegistry.register("rss", RSSConnector)
