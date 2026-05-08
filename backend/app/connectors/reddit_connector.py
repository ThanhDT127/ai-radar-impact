"""Reddit connector — fetches posts from a subreddit via the public .json endpoint."""

import logging

import httpx

from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.connectors.web_article_connector import WebArticleConnector
from app.models.source import Source

logger = logging.getLogger(__name__)

REDDIT_HEADERS = {"User-Agent": "AIRadarBot/1.0"}


class RedditConnector(BaseConnector):
    """Fetches posts from a Reddit subreddit and extracts full article content."""

    def __init__(self) -> None:
        self._web = WebArticleConnector()

    def fetch(self, source: Source) -> list[ConnectorEntry]:
        """Fetch subreddit posts, filter by upvotes, extract content."""
        config = source.config or {}
        max_items: int = config.get("max_items", 25)
        min_upvotes: int = config.get("min_upvotes", 20)
        fetch_timeout: int = config.get("fetch_timeout", 10)
        subreddit: str = config.get("subreddit", "MachineLearning")

        url = f"https://www.reddit.com/r/{subreddit}/.json?limit={max_items}"

        try:
            with httpx.Client(timeout=fetch_timeout, headers=REDDIT_HEADERS) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.error("Failed to fetch Reddit r/%s: %s", subreddit, e)
            return []

        posts = data.get("data", {}).get("children", [])
        entries: list[ConnectorEntry] = []

        for child in posts:
            post = child.get("data", {})

            ups: int = post.get("ups", 0)
            if ups < min_upvotes:
                continue

            title: str = post.get("title", "") or "Untitled"
            permalink: str = "https://www.reddit.com" + (post.get("permalink", "") or "")
            post_url: str = post.get("url", "") or ""
            is_self: bool = post.get("is_self", False)

            if is_self:
                raw_content = post.get("selftext", "") or ""
                if not raw_content or raw_content == "[removed]" or raw_content == "[deleted]":
                    logger.warning("Reddit self-post '%s' has no usable text — skipping", title[:60])
                    continue
                entries.append(ConnectorEntry(
                    source_url=permalink,
                    title=title,
                    raw_content=raw_content,
                    metadata={"upvotes": ups, "subreddit": subreddit},
                ))
            else:
                result = self._web.extract(post_url, timeout=fetch_timeout)
                if result is None:
                    logger.warning("Failed to extract article from Reddit post '%s' (%s) — skipping", title[:60], post_url)
                    continue
                entries.append(ConnectorEntry(
                    source_url=post_url,
                    title=title,
                    raw_content=result.content,
                    author=result.author,
                    metadata={"upvotes": ups, "subreddit": subreddit, "reddit_permalink": permalink},
                ))

        logger.info("Reddit r/%s: fetched %d entries (min_upvotes=%d)", subreddit, len(entries), min_upvotes)
        return entries


ConnectorRegistry.register("reddit", RedditConnector)
