"""PlaywrightConnector — headless Chromium / CloakBrowser scraper for JS-rendered sites."""

import hashlib
import logging
import os
import random
import re
import tempfile
import threading
import time
from urllib.parse import urljoin, urlparse

import trafilatura
from playwright.sync_api import sync_playwright

from app.config import settings
from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.models.source import Source

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Login-wall detection (W3/T8): URL markers hệ thống bị đẩy về khi phiên hết hạn.
LOGIN_WALL_URL_MARKERS = {
    "linkedin.com": ("/authwall", "/login", "/checkpoint", "/uas/login"),
    "x.com": ("/i/flow/login", "/login", "/account/access"),
    "twitter.com": ("/i/flow/login", "/login", "/account/access"),
}
# Selector form đăng nhập đặc trưng (fallback khi URL không đổi nhưng trang là login).
LOGIN_FORM_SELECTOR = (
    "input[name='session_key'], input[name='session_password'], "
    "input[name='text'][autocomplete='username']"
)
# Login URL để in kèm hướng dẫn tạo lại session bằng codegen.
LOGIN_URLS = {
    "linkedin.com": "https://www.linkedin.com/login",
    "x.com": "https://x.com/login",
    "twitter.com": "https://x.com/login",
}


def _login_url_for(index_url: str) -> str:
    host = urlparse(index_url).netloc.lower()
    for domain, url in LOGIN_URLS.items():
        if domain in host:
            return url
    return "<login-url>"


class PlaywrightConnector(BaseConnector):
    """Fetch articles from SPA/JS-rendered pages via CloakBrowser (CDP) or headless Chromium.

    Config:
      - link_selector (str): CSS selector for article links / feed cards (default: "a")
      - link_pattern (str|list): regex(es) matched against href to filter links (default: "")
      - max_items (int): max articles/cards to fetch per run (default: 10)
      - wait_for (str): CSS selector to wait for before extracting (default: "")
      - wait_timeout (int): timeout ms for wait_for (default: 10000)
      - cookie_file (str): path to storage_state JSON for authenticated sessions
      - auto_scroll_count (int): number of scroll-to-bottom passes (default: 0)
      - extract_from_feed (bool): scrape feed cards directly instead of following links
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
        # Trạng thái phiên chia sẻ với các helper — quyết định có sliding-refresh không.
        session = {"login_wall": False, "cookie_file": cookie_file, "source_name": source.name}

        def _run() -> None:
            try:
                with sync_playwright() as pw:
                    browser, launched_local = self._connect_browser(pw)
                    context = self._new_context(browser, launched_local, cookie_file)
                    try:
                        if extract_from_feed:
                            entries = self._extract_feed_cards(
                                context, index_url, link_selector, max_items,
                                wait_for, wait_timeout, auto_scroll_count, session,
                            )
                            logger.info("Playwright feed extracted %d cards from %s", len(entries), index_url)
                        else:
                            urls = self._extract_links(
                                context, index_url, link_selector, link_pattern,
                                max_items, wait_for, wait_timeout, auto_scroll_count, session,
                            )
                            if not urls:
                                if not session["login_wall"]:
                                    logger.warning(
                                        "Playwright matched 0 article URLs at %s (pattern=%r)",
                                        index_url, link_pattern,
                                    )
                                entries = []
                            else:
                                entries = self._fetch_articles(context, urls, index_url)
                                logger.info("Playwright fetched %d entries from %s", len(entries), index_url)

                        result.extend(entries)

                        # Sliding refresh (T8/D5): gia hạn cookie sau phiên THÀNH CÔNG.
                        if cookie_file and result and not session["login_wall"]:
                            self._save_storage_state(context, cookie_file)
                    finally:
                        # Luôn đóng context (chống leak trong CloakBrowser chạy dài hạn).
                        try:
                            context.close()
                        except Exception:
                            pass
                        # Chỉ kill browser khi TỰ launch local; qua CDP chỉ disconnect,
                        # không đóng browser dùng chung của CloakBrowser.
                        if launched_local:
                            try:
                                browser.close()
                            except Exception:
                                pass
            except Exception as e:
                exc_holder.append(e)

        # sync_playwright() cannot run inside an asyncio event loop — use a dedicated thread
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=180)

        if exc_holder:
            logger.error("Playwright connector failed for source '%s': %s", source.name, exc_holder[0])
        return result

    # --- Browser / context lifecycle ---------------------------------------

    def _connect_browser(self, pw):
        """Return (browser, launched_local). Ưu tiên CloakBrowser qua CDP nếu cấu hình."""
        cdp_url = (settings.cloak_cdp_url or "").strip()
        if cdp_url:
            try:
                browser = pw.chromium.connect_over_cdp(cdp_url)
                logger.info("Connected to CloakBrowser via CDP at %s", cdp_url)
                return browser, False
            except Exception as e:
                logger.warning(
                    "CloakBrowser CDP (%s) không kết nối được (%s) — fallback Chromium local.",
                    cdp_url, e,
                )
        else:
            logger.info("CLOAK_CDP_URL rỗng — dùng Chromium local trực tiếp.")

        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        return browser, True

    def _new_context(self, browser, launched_local: bool, cookie_file: str):
        context_options: dict = {}
        if cookie_file:
            if os.path.exists(cookie_file):
                context_options["storage_state"] = cookie_file
            else:
                logger.warning(
                    "cookie_file %s không tồn tại — thử fetch không auth "
                    "(sẽ báo login-wall nếu trang yêu cầu đăng nhập)", cookie_file,
                )
        # D2: chỉ ép user-agent tĩnh khi Chromium local. Qua CloakBrowser thì để nó
        # tự quản fingerprint — UA tĩnh lệch version Chromium thật là tín hiệu bot.
        if launched_local:
            context_options["user_agent"] = USER_AGENT
        return browser.new_context(**context_options)

    def _save_storage_state(self, context, cookie_file: str) -> None:
        """Ghi đè cookie_file bằng storage_state hiện tại (atomic: tạm + rename)."""
        try:
            directory = os.path.dirname(cookie_file) or "."
            os.makedirs(directory, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
            os.close(fd)
            context.storage_state(path=tmp)
            os.replace(tmp, cookie_file)
            logger.info("Sliding refresh: gia hạn storage_state -> %s", cookie_file)
        except Exception as e:
            logger.warning("Không lưu được storage_state vào %s: %s", cookie_file, e)

    # --- Anti-bot helpers ---------------------------------------------------

    def _is_login_wall(self, page, index_url: str) -> bool:
        """Phát hiện trang bị chặn bởi login-wall (redirect login hoặc login form)."""
        host = urlparse(index_url).netloc.lower()
        current = (page.url or "").lower()
        for domain, markers in LOGIN_WALL_URL_MARKERS.items():
            if domain in host and any(m in current for m in markers):
                return True
        try:
            if page.query_selector(LOGIN_FORM_SELECTOR):
                return True
        except Exception:
            pass
        return False

    def _log_login_wall(self, source_name: str, index_url: str, cookie_file: str) -> None:
        logger.error(
            "Login-wall tại nguồn '%s' (%s) — phiên đăng nhập hết hạn hoặc thiếu. "
            "Tạo lại session: playwright codegen --save-storage=%s %s",
            source_name, index_url, cookie_file or "<cookie_file>", _login_url_for(index_url),
        )

    def _article_delay_seconds(self) -> float:
        """Delay giữa các bài trong một phiên (base + jitter) — nhịp giống người."""
        return settings.ingest_article_delay_seconds + random.uniform(0, settings.ingest_jitter_seconds)

    def _dedup_by_content(self, entries: list[ConnectorEntry]) -> list[ConnectorEntry]:
        """Loại entry trùng hệt nội dung trong cùng batch (chặn 'N bản sao trang shell')."""
        seen: set[str] = set()
        kept: list[ConnectorEntry] = []
        for e in entries:
            h = hashlib.sha256((e.raw_content or "").encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            kept.append(e)
        dropped = len(entries) - len(kept)
        if dropped:
            logger.warning(
                "Guard trùng content: loại %d/%d entry trùng nội dung trong batch",
                dropped, len(entries),
            )
        return kept

    # --- Extraction ---------------------------------------------------------

    def _extract_feed_cards(
        self,
        context,
        index_url: str,
        card_selector: str,
        max_items: int,
        wait_for: str,
        wait_timeout: int,
        auto_scroll_count: int,
        session: dict,
    ) -> list[ConnectorEntry]:
        page = context.new_page()
        entries: list[ConnectorEntry] = []
        try:
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page.goto(index_url, wait_until="domcontentloaded", timeout=30000)

            if self._is_login_wall(page, index_url):
                self._log_login_wall(session["source_name"], index_url, session["cookie_file"])
                session["login_wall"] = True
                return []

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

                fake_hash = hashlib.md5(content[:50].encode()).hexdigest()
                url = f"{index_url}#feed-{fake_hash}"
                title = content.split('\n')[0][:100] + "..."
                entries.append(ConnectorEntry(
                    source_url=url,
                    title=title,
                    raw_content=content,
                    author=None,
                    published_at=None,
                    metadata={"index_url": index_url, "renderer": "playwright_feed"},
                ))
            return self._dedup_by_content(entries)
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
        session: dict,
    ) -> list[str]:
        page = context.new_page()
        try:
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page.goto(index_url, wait_until="domcontentloaded", timeout=30000)

            if self._is_login_wall(page, index_url):
                self._log_login_wall(session["source_name"], index_url, session["cookie_file"])
                session["login_wall"] = True
                return []

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
            for i, url in enumerate(urls):
                # Nhịp cào trong phiên (T8): nghỉ giữa các bài để giống người, tránh bị chặn.
                if i > 0:
                    time.sleep(self._article_delay_seconds())
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
        return self._dedup_by_content(entries)


ConnectorRegistry.register("playwright", PlaywrightConnector)
