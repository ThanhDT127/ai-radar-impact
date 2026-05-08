"""Web article extractor — trafilatura wrapper for extracting main content from URLs."""

import logging
from dataclasses import dataclass

import httpx
import trafilatura

logger = logging.getLogger(__name__)


@dataclass
class ArticleResult:
    """Extracted article content and metadata."""

    content: str
    author: str | None = None
    date: str | None = None
    title: str | None = None


class WebArticleConnector:
    """Extracts main article content from a URL using trafilatura.

    Not a BaseConnector — utility class used internally by HN/Reddit connectors.
    """

    def extract(self, url: str, timeout: int = 10) -> ArticleResult | None:
        """Fetch and extract main article content from URL.

        Returns ArticleResult on success, None if fetch or extraction fails.
        """
        try:
            downloaded = trafilatura.fetch_url(url)
        except Exception as e:
            logger.warning("Failed to fetch URL %s: %s", url, e)
            return None

        if not downloaded:
            logger.warning("Empty response from URL: %s", url)
            return None

        content = trafilatura.extract(
            downloaded,
            output_format="txt",
            include_comments=False,
            include_tables=True,
        )

        if not content:
            logger.warning("trafilatura extracted no content from: %s", url)
            return None

        metadata = trafilatura.extract_metadata(downloaded)
        author = metadata.author if metadata else None
        date = metadata.date if metadata else None
        title = metadata.title if metadata else None

        return ArticleResult(content=content, author=author, date=date, title=title)
