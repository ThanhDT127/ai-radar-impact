"""WebIndexConnector — scrape an index/listing page, extract article URLs, fetch each via trafilatura."""

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.connectors.web_article_connector import WebArticleConnector
from app.models.source import Source

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 AI-Radar-Impact-Bot/1.0"


class WebIndexConnector(BaseConnector):
    """Scrape index page for article links matching `link_pattern`, then extract each.

    Config:
      - link_pattern (str): regex matched against `href` to detect article links (default: any href under same domain)
      - link_selector (str, optional): CSS selector for narrowing (e.g. 'a.article-card')
      - max_items (int): default 10
      - exclude_patterns (list[str]): regex list to exclude (e.g. '/page/', '/tag/')
    """

    def __init__(self) -> None:
        self._article = WebArticleConnector()

    def fetch(self, source: Source) -> list[ConnectorEntry]:
        config = source.config or {}
        index_url = source.feed_url
        if not index_url:
            logger.warning("WebIndex source '%s' missing feed_url", source.name)
            return []

        link_pattern: str = config.get("link_pattern", "")
        link_selector: str = config.get("link_selector", "a")
        max_items: int = int(config.get("max_items", 10))
        exclude_patterns: list[str] = config.get("exclude_patterns", []) or []

        try:
            with httpx.Client(timeout=15.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
                resp = client.get(index_url)
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            logger.error("WebIndex fetch failed for %s: %s", index_url, e)
            return []

        try:
            soup = BeautifulSoup(html, "html.parser")
            anchors = soup.select(link_selector)
        except Exception as e:
            logger.warning("WebIndex parse failed for %s: %s", index_url, e)
            return []

        # Collect unique article URLs
        seen: set[str] = set()
        urls: list[str] = []
        base_domain = urlparse(index_url).netloc

        for a in anchors:
            href = (a.get("href") or "").strip()
            if not href:
                continue
            # Resolve relative URL
            full = urljoin(index_url, href)
            # Same-domain only
            if urlparse(full).netloc and urlparse(full).netloc != base_domain:
                continue
            # Match pattern
            if link_pattern and not re.search(link_pattern, full):
                continue
            # Exclude
            if any(re.search(p, full) for p in exclude_patterns):
                continue
            if full in seen:
                continue
            seen.add(full)
            urls.append(full)
            if len(urls) >= max_items:
                break

        if not urls:
            logger.warning("WebIndex matched 0 article URLs at %s (pattern=%r)", index_url, link_pattern)
            return []

        entries: list[ConnectorEntry] = []
        for url in urls:
            try:
                result = self._article.extract(url, timeout=15)
                if result is None:
                    continue
                if not result.content or len(result.content.strip()) < 100:
                    continue
                entries.append(
                    ConnectorEntry(
                        source_url=url,
                        title=result.title or url.rsplit("/", 1)[-1],
                        raw_content=result.content,
                        author=result.author,
                        published_at=None,
                        metadata={"index_url": index_url},
                    )
                )
            except Exception as e:
                logger.warning("WebIndex extract failed for %s: %s", url, e)
                continue

        logger.info("WebIndex fetched %d entries from %s", len(entries), index_url)
        return entries


ConnectorRegistry.register("web_index", WebIndexConnector)
