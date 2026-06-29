"""Verify seeded RSS feeds by fetching and parsing sample entries.

Usage:
    python -m app.scripts.verify_feeds
"""

from __future__ import annotations

import feedparser

from app.scripts.seed_sources import INITIAL_SOURCES


def main() -> int:
    failures = 0

    rss_sources = [
        s for s in INITIAL_SOURCES if s.get("source_type") == "rss" and s.get("feed_url")
    ]

    for index, source in enumerate(rss_sources, start=1):
        url = source["feed_url"]
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            failures += 1
            print(f"[FAIL] {index:02d}. {source['name']}: {url}")
            print(f"       parse error: {feed.bozo_exception}")
            continue

        sample = feed.entries[0] if feed.entries else {}
        print(f"[ OK ] {index:02d}. {source['name']}: {len(feed.entries)} items")
        print(f"       url: {url}")
        print(f"       title: {sample.get('title', 'n/a')}")
        print(f"       author: {sample.get('author', 'n/a')}")
        if feed.bozo:
            print(f"       warning: {feed.bozo_exception}")

    return failures


if __name__ == "__main__":
    raise SystemExit(main())
