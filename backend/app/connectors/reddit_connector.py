"""Reddit connector — fetches posts from a subreddit via the public .rss endpoint."""

import logging
import re

from bs4 import BeautifulSoup
import feedparser
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
        """Fetch subreddit posts via RSS, filter and extract content."""
        config = source.config or {}
        max_items: int = config.get("max_items", 25)
        fetch_timeout: int = config.get("fetch_timeout", 10)
        subreddit: str = config.get("subreddit", "MachineLearning")

        url = f"https://www.reddit.com/r/{subreddit}/.rss"

        try:
            with httpx.Client(timeout=fetch_timeout, headers=REDDIT_HEADERS) as client:
                resp = client.get(url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)
        except Exception as e:
            logger.error("Failed to fetch Reddit r/%s RSS: %s", subreddit, e)
            return []

        entries: list[ConnectorEntry] = []

        for entry in feed.entries[:max_items]:
            try:
                title: str = entry.get("title", "") or "Untitled"
                permalink: str = entry.get("link", "") or ""

                # Parse summary HTML to find external links
                summary_html = entry.get("summary", "") or ""
                soup = BeautifulSoup(summary_html, "html.parser")

                # Extract link tag [link]
                # Format: <span><a href="post_url">[link]</a></span>
                link_tag = soup.find("a", string="[link]")
                post_url = link_tag.get("href", "") if link_tag else permalink

                # If post_url is equal to permalink (or it's a reddit comments page), it's a self-post
                is_self = (post_url == permalink) or (
                    "reddit.com/r/" in post_url and "/comments/" in post_url
                )

                if is_self:
                    # Self-post: extract text content directly from summary HTML
                    md_div = soup.find("div", class_="md")
                    raw_content = md_div.get_text(separator=" ") if md_div else soup.get_text()

                    # Collapse whitespace
                    raw_content = re.sub(r"\s+", " ", raw_content).strip()

                    if (
                        not raw_content
                        or raw_content == "[removed]"
                        or raw_content == "[deleted]"
                    ):
                        logger.warning(
                            "Reddit self-post '%s' has no usable text — skipping", title[:60]
                        )
                        continue

                    entries.append(
                        ConnectorEntry(
                            source_url=permalink,
                            title=title,
                            raw_content=raw_content,
                            author=entry.get("author"),
                            metadata={"subreddit": subreddit, "is_self": True},
                        )
                    )
                else:
                    # Link-post: fetch external page using WebArticleConnector
                    result = self._web.extract(post_url, timeout=fetch_timeout)
                    if result is None:
                        logger.warning(
                            "Failed to extract article from Reddit link post '%s' (%s) — skipping",
                            title[:60],
                            post_url,
                        )
                        continue

                    entries.append(
                        ConnectorEntry(
                            source_url=post_url,
                            title=title,
                            raw_content=result.content,
                            author=result.author or entry.get("author"),
                            metadata={
                                "subreddit": subreddit,
                                "reddit_permalink": permalink,
                                "is_self": False,
                            },
                        )
                    )
            except Exception as e:
                logger.warning(
                    "Failed to process Reddit RSS entry '%s': %s", entry.get("title", ""), e
                )

        logger.info("Reddit r/%s: fetched %d entries via RSS", subreddit, len(entries))
        return entries


ConnectorRegistry.register("reddit", RedditConnector)

