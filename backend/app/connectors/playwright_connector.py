"""PlaywrightConnector — headless Chromium scraper for JavaScript-rendered SPA sites."""

import logging
import re
import threading
from urllib.parse import urljoin, urlparse

import trafilatura
from playwright.sync_api import sync_playwright

from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.models.source import Source

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class PlaywrightConnector(BaseConnector):
    """Fetch articles from SPA/JavaScript-rendered pages using headless Chromium.

    Config:
      - link_selector (str): CSS selector for article links on listing page (default: "a")
      - link_pattern (str): regex matched against href to filter article links (default: "")
      - max_items (int): max articles to fetch per run (default: 10)
      - wait_for (str): CSS selector to wait for before extracting links (default: "")
      - wait_timeout (int): timeout ms for wait_for (default: 10000)
    """

    def fetch(self, source: Source) -> list[ConnectorEntry]:
        config = source.config or {}
        index_url: str = source.feed_url or ""
        if not index_url:
            logger.warning("Playwright source '%s' missing feed_url", source.name)
            return []

        link_selector: str = config.get("link_selector", "a")
        link_pattern: str = config.get("link_pattern", "")
        max_items: int = int(config.get("max_items", 10))
        wait_for: str = config.get("wait_for", "")
        wait_timeout: int = int(config.get("wait_timeout", 10000))

        result: list[ConnectorEntry] = []
        exc_holder: list[Exception] = []

        def _run() -> None:
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-dev-shm-usage"],
                    )
                    urls = self._extract_links(
                        browser, index_url, link_selector, link_pattern,
                        max_items, wait_for, wait_timeout,
                    )
                    if not urls:
                        logger.warning(
                            "Playwright matched 0 article URLs at %s (pattern=%r)",
                            index_url, link_pattern,
                        )
                        return
                    entries = self._fetch_articles(browser, urls, index_url)
                    result.extend(entries)
                    logger.info("Playwright fetched %d entries from %s", len(entries), index_url)
            except Exception as e:
                exc_holder.append(e)

        # sync_playwright() cannot run inside an asyncio event loop — use a dedicated thread
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=180)

        if exc_holder:
            logger.error("Playwright connector failed for source '%s': %s", source.name, exc_holder[0])
        return result

    def _extract_links(
        self,
        browser,
        index_url: str,
        link_selector: str,
        link_pattern: str,
        max_items: int,
        wait_for: str,
        wait_timeout: int,
    ) -> list[str]:
        page = browser.new_page(user_agent=USER_AGENT)
        try:
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page.goto(index_url, wait_until="domcontentloaded", timeout=30000)
            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=wait_timeout)
                except Exception:
                    logger.warning("wait_for selector '%s' timed out on %s", wait_for, index_url)

            anchors = page.query_selector_all(link_selector)
            base_domain = urlparse(index_url).netloc
            seen: set[str] = set()
            urls: list[str] = []

            for a in anchors:
                if len(urls) >= max_items:
                    break
                href = (a.get_attribute("href") or "").strip()
                if not href:
                    continue
                full = urljoin(index_url, href)
                parsed = urlparse(full)
                if parsed.netloc and parsed.netloc != base_domain:
                    continue
                if link_pattern and not re.search(link_pattern, full):
                    continue
                if full in seen:
                    continue
                seen.add(full)
                urls.append(full)

            return urls
        except Exception as e:
            logger.error("Playwright failed to load listing page %s: %s", index_url, e)
            return []
        finally:
            page.close()

    def _fetch_articles(self, browser, urls: list[str], index_url: str) -> list[ConnectorEntry]:
        entries: list[ConnectorEntry] = []
        page = browser.new_page(user_agent=USER_AGENT)
        try:
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            for url in urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    html = page.content()
                    content = trafilatura.extract(
                        html,
                        include_comments=False,
                        include_tables=False,
                        no_fallback=False,
                    )
                    if not content or len(content.strip()) < 100:
                        logger.debug("Playwright: trafilatura extracted nothing for %s", url)
                        continue

                    title = page.title() or url.rsplit("/", 1)[-1]
                    entries.append(
                        ConnectorEntry(
                            source_url=url,
                            title=title,
                            raw_content=content,
                            author=None,
                            published_at=None,
                            metadata={"index_url": index_url, "renderer": "playwright"},
                        )
                    )
                except Exception as e:
                    logger.warning("Playwright: failed to fetch article %s: %s", url, e)
                    continue
        finally:
            page.close()
        return entries


ConnectorRegistry.register("playwright", PlaywrightConnector)
