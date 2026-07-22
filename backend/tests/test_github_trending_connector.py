"""Tests for GitHubTrendingConnector README enrichment + cross-window dedup (w2-github-readme)."""

import httpx
import pytest
from bs4 import BeautifulSoup

import app.connectors.github_trending_connector as gh
from app.connectors.github_trending_connector import (
    README_MAX_CHARS,
    GitHubTrendingConnector,
)
from app.services.normalizer import make_fingerprint

# Minimal trending article fragment matching the selectors used in _parse_repo.
ARTICLE_HTML = """
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/acme/widget">acme / widget</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">A fast widget toolkit.</p>
  <span itemprop="programmingLanguage">Python</span>
  <a class="Link--muted d-inline-block mr-3" href="/acme/widget/stargazers">12,345</a>
  <a class="Link--muted d-inline-block mr-3" href="/acme/widget/network/members">678</a>
  <span class="d-inline-block float-sm-right">250 stars today</span>
</article>
"""


def _article():
    return BeautifulSoup(ARTICLE_HTML, "html.parser").select_one("article.Box-row")


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


class _FakeClient:
    """Stand-in for httpx.Client that routes GETs through a handler(url) -> _FakeResponse."""

    def __init__(self, handler):
        self._handler = handler

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url, **kwargs):
        return self._handler(url)


def _patch_readme(monkeypatch, handler):
    monkeypatch.setattr(gh.httpx, "Client", lambda *a, **k: _FakeClient(handler))


def test_readme_enrichment_appends_and_truncates(monkeypatch):
    """3.1 — README fetch OK → raw_content chứa README, cắt ≤ README_MAX_CHARS."""
    long_readme = "X" * (README_MAX_CHARS + 1000)

    def handler(url: str):
        if "README.md" in url:
            return _FakeResponse(200, long_readme)
        return _FakeResponse(404)

    _patch_readme(monkeypatch, handler)

    entry = GitHubTrendingConnector()._parse_repo(_article(), since="daily", position=1)

    assert entry is not None
    assert "README:" in entry.raw_content
    # Metadata block stays before README so the 6000-char prompt cut spares core signal.
    assert entry.raw_content.index("acme/widget") < entry.raw_content.index("README:")
    # Truncated to exactly README_MAX_CHARS chars of body.
    assert "X" * README_MAX_CHARS in entry.raw_content
    assert "X" * (README_MAX_CHARS + 1) not in entry.raw_content


def test_readme_fetch_failsafe_keeps_description(monkeypatch):
    """3.2 — Mọi filename 404 → giữ content mô tả cũ, không exception, entry vẫn hợp lệ."""

    def handler(url: str):
        return _FakeResponse(404)

    _patch_readme(monkeypatch, handler)

    entry = GitHubTrendingConnector()._parse_repo(_article(), since="daily", position=1)

    assert entry is not None
    assert "README:" not in entry.raw_content
    assert "A fast widget toolkit." in entry.raw_content


def test_readme_disabled_by_config(monkeypatch):
    """1.3 — fetch_readme=False → không fetch, content chỉ có metadata."""

    def handler(url: str):  # pragma: no cover - phải không bao giờ gọi tới
        raise AssertionError("README must not be fetched when fetch_readme=False")

    _patch_readme(monkeypatch, handler)

    entry = GitHubTrendingConnector()._parse_repo(
        _article(), since="daily", position=1, fetch_readme=False
    )

    assert entry is not None
    assert "README:" not in entry.raw_content


def test_fingerprint_stable_across_trend_windows(monkeypatch):
    """3.3 — Cùng owner/repo, khác `since` và khác README → fingerprint BẰNG NHAU."""

    def handler_daily(url: str):
        return _FakeResponse(200, "daily readme body")

    def handler_weekly(url: str):
        return _FakeResponse(200, "totally different weekly readme body")

    _patch_readme(monkeypatch, handler_daily)
    entry_daily = GitHubTrendingConnector()._parse_repo(_article(), since="daily", position=1)

    _patch_readme(monkeypatch, handler_weekly)
    entry_weekly = GitHubTrendingConnector()._parse_repo(_article(), since="weekly", position=7)

    # raw_content khác nhau (README khác + cửa sổ khác) nhưng fingerprint chỉ tính source_url + title.
    assert entry_daily.raw_content != entry_weekly.raw_content
    fp_daily = make_fingerprint(entry_daily.source_url, entry_daily.title)
    fp_weekly = make_fingerprint(entry_weekly.source_url, entry_weekly.title)
    assert fp_daily == fp_weekly
