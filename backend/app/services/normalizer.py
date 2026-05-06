"""Normalizer service — cleans HTML and generates content fingerprints."""

import hashlib
import logging
import re

from bs4 import BeautifulSoup

from app.connectors.rss_connector import FeedEntry

logger = logging.getLogger(__name__)

# Max characters to keep for normalized content
MAX_CONTENT_LENGTH = 8000


def clean_html(html: str) -> str:
    """Strip HTML tags and normalize whitespace from content.

    Returns plain text, truncated to MAX_CONTENT_LENGTH chars.
    """
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # Remove script/style elements
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_CONTENT_LENGTH]


def make_fingerprint(source_url: str, title: str) -> str:
    """Generate a SHA-256 fingerprint for deduplication.

    Based on URL + title to detect duplicate entries.
    """
    raw = f"{source_url.strip().lower()}::{title.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_entry(entry: FeedEntry) -> tuple[str, str]:
    """Normalize a FeedEntry.

    Returns (normalized_content, fingerprint).
    """
    normalized_content = clean_html(entry.raw_content)
    fingerprint = make_fingerprint(entry.source_url, entry.title)
    return normalized_content, fingerprint
