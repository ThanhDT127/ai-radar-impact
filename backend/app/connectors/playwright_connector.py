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
        link_pattern = config.get("link_pattern", "")
        max_items: int = int(config.get("max_items", 10))
        wait_for: str = config.get("wait_for", "")
        wait_timeout: int = int(config.get("wait_timeout", 10000))
        cookie_file: str = config.get("cookie_file", "")
        auto_scroll_count: int = int(config.get("auto_scroll_count", 0))
        extract_from_feed: bool = config.get("extract_from_feed", False)

        result: list[ConnectorEntry] = []
        exc_holder: list[Exception] = []

        def _run() -> None:
            try:
                with sync_playwright() as pw:
                    # Attempt to connect to CloakBrowser via CDP
                    try:
                        browser = pw.chromium.connect_over_cdp("http://cloak:9222")
                        logger.info("Successfully connected to CloakBrowser via CDP")
                    except Exception as e:
                        logger.warning("Failed to connect to CloakBrowser (%s). Falling back to local Chromium.", e)
                        browser = pw.chromium.launch(
                            headless=True,
                            args=["--no-sandbox", "--disable-dev-shm-usage"],
                        )
                    
                    context_options = {}
                    if cookie_file:
                        import os
                        if os.path.exists(cookie_file):
                            context_options["storage_state"] = cookie_file
                        else:
                            logger.warning("cookie_file %s not found, continuing without auth", cookie_file)
                    
                    context = browser.new_context(user_agent=USER_AGENT, **context_options)

                    if extract_from_feed:
                        entries = self._extract_feed_cards(
                            context, index_url, link_selector, max_items, wait_for, wait_timeout, auto_scroll_count
                        )
                        result.extend(entries)
                        logger.info("Playwright feed extracted %d cards from %s", len(entries), index_url)
                    else:
                        urls = self._extract_links(
                            context, index_url, link_selector, link_pattern,
                            max_items, wait_for, wait_timeout, auto_scroll_count
                        )
                        if not urls:
                            logger.warning(
                                "Playwright matched 0 article URLs at %s (pattern=%r)",
                                index_url, link_pattern,
                            )
                            return
                        entries = self._fetch_articles(context, urls, index_url)
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

    def _extract_feed_cards(
        self,
        context,
        index_url: str,
        card_selector: str,
        max_items: int,
        wait_for: str,
        wait_timeout: int,
        auto_scroll_count: int,
    ) -> list[ConnectorEntry]:
        page = context.new_page()
        entries: list[ConnectorEntry] = []
        try:
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page.goto(index_url, wait_until="domcontentloaded", timeout=30000)
            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=wait_timeout)
                except Exception:
                    pass

            for _ in range(auto_scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

            cards = page.query_selector_all(card_selector)
            for card in cards:
                if len(entries) >= max_items:
                    break
                content = (card.inner_text() or "").strip()
                if len(content) < 100:
                    continue
                
                import hashlib
                fake_hash = hashlib.md5(content[:50].encode()).hexdigest()
                url = f"{index_url}#feed-{fake_hash}"
                title = content.split('\n')[0][:100] + "..."
                entries.append(ConnectorEntry(
                    source_url=url,
                    title=title,
                    raw_content=content,
                    author=None,
                    published_at=None,
                    metadata={"index_url": index_url, "renderer": "playwright_feed"}
                ))
            return entries
        except Exception as e:
            logger.error("Playwright feed extraction failed: %s", e)
            return []
        finally:
            page.close()

    def _extract_links(
        self,
        context,
        index_url: str,
        link_selector: str,
        link_pattern,
        max_items: int,
        wait_for: str,
        wait_timeout: int,
        auto_scroll_count: int,
    ) -> list[str]:
        page = context.new_page()
        try:
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page.goto(index_url, wait_until="domcontentloaded", timeout=30000)
            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=wait_timeout)
                except Exception:
                    logger.warning("wait_for selector '%s' timed out on %s", wait_for, index_url)

            for _ in range(auto_scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

            anchors = page.query_selector_all(link_selector)
            base_domain = urlparse(index_url).netloc
            seen: set[str] = set()
            urls: list[str] = []
            
            patterns = [link_pattern] if isinstance(link_pattern, str) and link_pattern else link_pattern if isinstance(link_pattern, list) else []

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
                
                if patterns:
                    matched = False
                    for p in patterns:
                        if re.search(p, full):
                            matched = True
                            break
                    if not matched:
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

    def _fetch_articles(self, context, urls: list[str], index_url: str) -> list[ConnectorEntry]:
        entries: list[ConnectorEntry] = []
        page = context.new_page()
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
