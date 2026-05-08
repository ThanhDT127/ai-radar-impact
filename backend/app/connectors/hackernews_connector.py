"""HackerNews connector — fetches top stories via HN Firebase API."""

import logging

import httpx

from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.connectors.web_article_connector import WebArticleConnector
from app.models.source import Source

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


class HackerNewsConnector(BaseConnector):
    """Fetches top stories from HackerNews and extracts full article content."""

    def __init__(self) -> None:
        self._web = WebArticleConnector()

    def fetch(self, source: Source) -> list[ConnectorEntry]:
        """Fetch top HN stories, filter by score, extract full articles."""
        config = source.config or {}
        max_items: int = config.get("max_items", 15)
        min_score: int = config.get("min_score", 50)
        fetch_timeout: int = config.get("fetch_timeout", 10)

        try:
            with httpx.Client(timeout=fetch_timeout) as client:
                resp = client.get(f"{HN_API_BASE}/topstories.json")
                resp.raise_for_status()
                story_ids: list[int] = resp.json()
        except Exception as e:
            logger.error("Failed to fetch HN top stories: %s", e)
            return []

        entries: list[ConnectorEntry] = []
        fetched = 0

        for story_id in story_ids:
            if fetched >= max_items:
                break

            try:
                with httpx.Client(timeout=fetch_timeout) as client:
                    resp = client.get(f"{HN_API_BASE}/item/{story_id}.json")
                    resp.raise_for_status()
                    item = resp.json()
            except Exception as e:
                logger.warning("Failed to fetch HN item %s: %s", story_id, e)
                continue

            if not item or item.get("type") != "story":
                continue

            score: int = item.get("score", 0)
            if score < min_score:
                continue

            title: str = item.get("title", "") or "Untitled"
            url: str = item.get("url", "")
            hn_permalink = f"https://news.ycombinator.com/item?id={story_id}"

            # Self-post (Ask HN / Show HN) — no external URL
            if not url:
                raw_content = item.get("text", "") or ""
                if not raw_content:
                    logger.warning("HN item %s has no URL and no text — skipping", story_id)
                    continue
                entries.append(ConnectorEntry(
                    source_url=hn_permalink,
                    title=title,
                    raw_content=raw_content,
                    metadata={"hn_score": score, "hn_id": story_id},
                ))
                fetched += 1
                continue

            # External link — extract full article
            result = self._web.extract(url, timeout=fetch_timeout)
            if result is None:
                logger.warning("Failed to extract article from HN story %s (%s) — skipping", story_id, url)
                continue

            entries.append(ConnectorEntry(
                source_url=url,
                title=title,
                raw_content=result.content,
                author=result.author,
                metadata={"hn_score": score, "hn_id": story_id, "hn_permalink": hn_permalink},
            ))
            fetched += 1

        logger.info("HackerNews: fetched %d entries (min_score=%d)", len(entries), min_score)
        return entries


ConnectorRegistry.register("hackernews", HackerNewsConnector)
