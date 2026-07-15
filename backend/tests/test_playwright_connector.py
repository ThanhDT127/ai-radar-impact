"""Tests for PlaywrightConnector anti-bot helpers (w3-anti-bot-crawl).

Chỉ test các helper thuần logic — không cần browser thật:
- guard trùng content trong batch (T7/3.4)
- delay giữa các bài trong phiên (T7/3.3)
- login-wall detection + login URL mapping (T8/4.1)
- sliding refresh ghi atomic (T8/4.2)
"""

import json

import pytest

from app.config import settings
from app.connectors.base import ConnectorEntry
from app.connectors.playwright_connector import (
    PlaywrightConnector,
    _login_url_for,
)


def _entry(content: str, url: str = "https://ex.com/a") -> ConnectorEntry:
    return ConnectorEntry(source_url=url, title="t", raw_content=content)


class _FakePage:
    """Trang giả cho _is_login_wall — chỉ cần .url và .query_selector."""

    def __init__(self, url: str, has_login_form: bool = False):
        self.url = url
        self._has_login_form = has_login_form

    def query_selector(self, selector: str):
        return object() if self._has_login_form else None


class _FakeContext:
    """Context giả cho _save_storage_state — ghi JSON như Playwright thật."""

    def storage_state(self, path: str):
        state = {"cookies": [{"name": "li_at", "value": "abc"}], "origins": []}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f)
        return state


# --- 3.4 dedup trùng content -------------------------------------------------

def test_dedup_drops_identical_content():
    """N entry cùng nội dung (trang shell) → chỉ giữ 1."""
    entries = [_entry("SAME BODY", url=f"https://ex.com/{i}") for i in range(16)]
    kept = PlaywrightConnector()._dedup_by_content(entries)
    assert len(kept) == 1


def test_dedup_keeps_distinct_content():
    """Nội dung khác nhau → giữ nguyên tất cả."""
    entries = [_entry(f"body-{i}") for i in range(5)]
    kept = PlaywrightConnector()._dedup_by_content(entries)
    assert len(kept) == 5


def test_dedup_empty_batch():
    assert PlaywrightConnector()._dedup_by_content([]) == []


# --- 3.3 delay giữa các bài --------------------------------------------------

def test_article_delay_within_configured_range():
    conn = PlaywrightConnector()
    base = settings.ingest_article_delay_seconds
    jitter = settings.ingest_jitter_seconds
    for _ in range(50):
        d = conn._article_delay_seconds()
        assert base <= d <= base + jitter


# --- 4.1 login-wall detection ------------------------------------------------

@pytest.mark.parametrize(
    "index_url, page_url",
    [
        ("https://www.linkedin.com/company/openai/posts/", "https://www.linkedin.com/authwall?trk=x"),
        ("https://www.linkedin.com/company/openai/posts/", "https://www.linkedin.com/login"),
        ("https://x.com/OpenAI", "https://x.com/i/flow/login"),
        ("https://x.com/OpenAI", "https://x.com/login"),
    ],
)
def test_login_wall_detected_by_redirect_url(index_url, page_url):
    page = _FakePage(page_url)
    assert PlaywrightConnector()._is_login_wall(page, index_url) is True


def test_login_wall_detected_by_form_selector():
    # URL không đổi nhưng có login form → vẫn coi là login-wall.
    page = _FakePage("https://www.linkedin.com/company/openai/posts/", has_login_form=True)
    assert PlaywrightConnector()._is_login_wall(page, "https://www.linkedin.com/company/openai/posts/") is True


def test_no_login_wall_on_normal_page():
    page = _FakePage("https://www.linkedin.com/company/openai/posts/")
    assert PlaywrightConnector()._is_login_wall(page, "https://www.linkedin.com/company/openai/posts/") is False


@pytest.mark.parametrize(
    "index_url, expected",
    [
        ("https://www.linkedin.com/company/openai/posts/", "https://www.linkedin.com/login"),
        ("https://x.com/OpenAI", "https://x.com/login"),
        ("https://example.com/blog", "<login-url>"),
    ],
)
def test_login_url_mapping(index_url, expected):
    assert _login_url_for(index_url) == expected


# --- 4.2 sliding refresh ghi atomic -----------------------------------------

def test_save_storage_state_writes_file(tmp_path):
    cookie_file = tmp_path / "linkedin_state.json"
    PlaywrightConnector()._save_storage_state(_FakeContext(), str(cookie_file))
    assert cookie_file.exists()
    data = json.loads(cookie_file.read_text())
    assert any(c["name"] == "li_at" for c in data["cookies"])
    # Không để lại file .tmp rác trong thư mục.
    assert list(tmp_path.glob("*.tmp")) == []


def test_save_storage_state_swallows_errors(tmp_path):
    """Lỗi ghi (context hỏng) không được raise ra ngoài — chỉ log warning."""
    class _BrokenContext:
        def storage_state(self, path: str):
            raise RuntimeError("boom")

    cookie_file = tmp_path / "x_state.json"
    # Không raise là pass.
    PlaywrightConnector()._save_storage_state(_BrokenContext(), str(cookie_file))
    assert not cookie_file.exists()
