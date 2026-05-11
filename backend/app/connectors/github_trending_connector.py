"""GitHub Trending connector — scrapes github.com/trending HTML to surface trending repos."""

import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.models.source import Source

logger = logging.getLogger(__name__)

TRENDING_BASE = "https://github.com/trending"
USER_AGENT = "AI-Radar-Impact-Bot/1.0 (+contact: rangdong)"


def _parse_stars(text: str) -> int:
    """Parse 'N stars today' / '1.2k stars this week' → int."""
    if not text:
        return 0
    m = re.search(r"([\d.,]+\s*k?)", text.strip(), re.IGNORECASE)
    if not m:
        return 0
    raw = m.group(1).replace(",", "").strip().lower()
    try:
        if raw.endswith("k"):
            return int(float(raw[:-1]) * 1000)
        return int(float(raw))
    except ValueError:
        return 0


def _parse_int(text: str) -> int:
    if not text:
        return 0
    raw = re.sub(r"[^\d]", "", text)
    try:
        return int(raw) if raw else 0
    except ValueError:
        return 0


class GitHubTrendingConnector(BaseConnector):
    """Scrape github.com/trending HTML and emit ConnectorEntry per repo."""

    def fetch(self, source: Source) -> list[ConnectorEntry]:
        config = source.config or {}
        language: str = config.get("language", "") or ""
        since: str = config.get("since", "daily")
        max_items: int = int(config.get("max_items", 25))

        url = f"{TRENDING_BASE}/{language}".rstrip("/")
        params = {"since": since}

        try:
            with httpx.Client(timeout=10.0, headers={"User-Agent": USER_AGENT}) as client:
                resp = client.get(url, params=params, follow_redirects=True)
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            logger.error("GitHub Trending fetch failed for %s?since=%s: %s", url, since, e)
            return []

        try:
            soup = BeautifulSoup(html, "html.parser")
            articles = soup.select("article.Box-row")
        except Exception as e:
            logger.warning("GitHub Trending HTML parse failed for %s: %s", url, e)
            return []

        if not articles:
            logger.warning(
                "GitHub Trending HTML selector matched 0 articles for %s — structure may have changed",
                url,
            )
            return []

        entries: list[ConnectorEntry] = []
        for position, article in enumerate(articles[:max_items], start=1):
            entry = self._parse_repo(article, since=since, position=position)
            if entry is not None:
                entries.append(entry)

        logger.info(
            "GitHub Trending fetched %d entries from %s?since=%s",
            len(entries), url, since,
        )
        return entries

    def _parse_repo(self, article, since: str, position: int) -> ConnectorEntry | None:
        try:
            link = article.select_one("h2.h3 a") or article.select_one("h2 a")
            if not link:
                return None
            href = link.get("href", "").strip()
            if not href.startswith("/"):
                return None
            # owner/repo derived from href "/owner/repo"
            parts = [p for p in href.strip("/").split("/") if p]
            if len(parts) < 2:
                return None
            owner, repo = parts[0], parts[1]
            full_name = f"{owner}/{repo}"

            desc_el = article.select_one("p.col-9, p.color-fg-muted")
            description = (desc_el.get_text(strip=True) if desc_el else "") or ""

            lang_el = article.select_one('[itemprop="programmingLanguage"]')
            language = lang_el.get_text(strip=True) if lang_el else ""

            # Stars total + forks
            stat_links = article.select("a.Link--muted")
            total_stars = 0
            forks = 0
            if stat_links:
                if len(stat_links) >= 1:
                    total_stars = _parse_int(stat_links[0].get_text())
                if len(stat_links) >= 2:
                    forks = _parse_int(stat_links[1].get_text())

            # Stars in period (today/this week/this month)
            period_el = article.select_one("span.d-inline-block.float-sm-right")
            stars_today = _parse_stars(period_el.get_text() if period_el else "")

            metadata = {
                "stars_today": stars_today,
                "total_stars": total_stars,
                "forks": forks,
                "language": language,
                "trend_window": since,
                "trending_position": position,
            }

            # Build rich content so analyzer has enough context (description alone often <200 chars)
            window_label = {"daily": "ngày", "weekly": "tuần", "monthly": "tháng"}.get(since, since)
            content_parts = [
                f"Repository {full_name} đang trending trên GitHub ({window_label}, vị trí #{position}).",
                f"Mô tả: {description}" if description else f"Repository {full_name} không có mô tả.",
                f"Ngôn ngữ chính: {language}." if language else "",
                f"Số sao tăng trong {window_label} này: {stars_today}.",
                f"Tổng sao: {total_stars}. Forks: {forks}.",
                f"Đây là tín hiệu sớm về một công cụ/thư viện đang được cộng đồng dev chú ý.",
            ]
            content = "\n\n".join(p for p in content_parts if p)

            return ConnectorEntry(
                source_url=f"https://github.com{href}",
                title=full_name,
                raw_content=content,
                author=None,
                published_at=None,
                metadata=metadata,
            )
        except Exception as e:
            logger.warning("Failed to parse trending repo at position %d: %s", position, e)
            return None


ConnectorRegistry.register("github_trending", GitHubTrendingConnector)
