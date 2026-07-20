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


class _FakeCard:
    """Feed card giả: `body` là nội dung selector thân bài (None = không có selector)."""

    def __init__(self, shell_text: str, body: str | None = None):
        self._shell = shell_text
        self._body = body

    def inner_text(self) -> str:
        return self._shell

    def query_selector(self, selector: str):
        if self._body is None:
            return None
        return _FakeCard(self._body)


# Vỏ thẻ thật của LinkedIn, hai lần cào cách nhau ít phút. Khác nhau đúng ở
# follower/reaction/comment/repost và trạng thái trình phát video — đo 20/07/2026.
def _shell(followers: str, reactions: str, comments: str, player: str) -> str:
    return (
        f"Feed post number 1\nOpenAI\nOpenAI\n{followers} followers\n{followers} followers\n"
        f"2d • \n \n2 days ago • Visible to anyone on or off LinkedIn\nFollow\n"
        f"Nội dung bài viết thật sự nằm ở đây và không đổi giữa các lần cào.\n"
        f"Dòng thứ hai của bài viết cũng giữ nguyên.\n"
        f"{player}\n{reactions}\n{comments} comments\n41 reposts"
    )


# --- dedup liên phiên: định danh phải ổn định giữa các lần cào ----------------

def test_card_body_prefers_selector():
    """Có selector thân bài thì dùng nó, bỏ hẳn vỏ thẻ."""
    card = _FakeCard(_shell("11,306,369", "490", "81", "Play"), body="Thân bài sạch")
    assert PlaywrightConnector()._card_body(card) == "Thân bài sạch"


def test_card_body_fallback_strips_volatile_lines():
    """Không có selector → lọc dòng biến động khỏi inner_text."""
    body = PlaywrightConnector()._card_body(_FakeCard(_shell("11,306,369", "490", "81", "Play")))
    assert "Nội dung bài viết thật sự" in body
    for noise in ("followers", "comments", "reposts", "Feed post number", "Play", "Follow"):
        assert noise not in body, f"còn sót dòng biến động: {noise}"


def test_card_body_stable_across_crawls():
    """Cùng một post, hai lần cào khác nhau về engagement → thân bài PHẢI giống nhau.

    Đây chính là bug đã quan sát: 35 document cho 6 post thật, vì hash tính trên
    `content[:50]` mà 50 ký tự đầu chứa số follower.
    """
    conn = PlaywrightConnector()
    first = conn._card_body(_FakeCard(_shell("11,306,369", "490", "81", "Play")))
    later = conn._card_body(_FakeCard(_shell("11,306,512", "494", "82", "Pause")))
    assert first == later, "thân bài đổi giữa 2 lần cào → sẽ nhân bản document"


def test_card_title_skips_accessibility_label():
    """Title lấy từ thân bài, không phải nhãn `Feed post number N`."""
    title = PlaywrightConnector()._card_title(
        PlaywrightConnector()._card_body(_FakeCard(_shell("11,306,369", "490", "81", "Play")))
    )
    assert not title.startswith("Feed post number")
    assert title.startswith("Nội dung bài viết thật sự")


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
        ("https://www.linkedin.com/in/andrewyng/recent-activity/shares/", "https://www.linkedin.com/checkpoint/lg/login"),
        ("https://www.linkedin.com/company/owasp/posts/", "https://www.linkedin.com/uas/login"),
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


def test_save_storage_state_keeps_old_file_when_auth_cookie_lost(tmp_path):
    """State mới rụng `li_at` → KHÔNG ghi đè, giữ phiên đang sống (regression 20/07).

    Quan sát thật: qua CDP CloakBrowser, `storage_state()` trả state thiếu `li_at`;
    ghi đè khiến lần cào kế tiếp dính authwall.
    """
    class _CtxWithoutAuth:
        def storage_state(self, path: str):
            state = {"cookies": [{"name": "JSESSIONID", "value": "x"}], "origins": []}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f)
            return state

    cookie_file = tmp_path / "linkedin_state.json"
    cookie_file.write_text(json.dumps({
        "cookies": [{"name": "li_at", "value": "alive"}, {"name": "JSESSIONID", "value": "x"}],
        "origins": [],
    }))
    PlaywrightConnector()._save_storage_state(_CtxWithoutAuth(), str(cookie_file))

    kept = json.loads(cookie_file.read_text())
    assert any(c["name"] == "li_at" for c in kept["cookies"]), "phiên bị ghi đè mất li_at"
    assert list(tmp_path.glob("*.tmp")) == []


def test_save_storage_state_writes_when_auth_cookie_kept(tmp_path):
    """State mới vẫn còn `li_at` → ghi đè bình thường (gia hạn cookie)."""
    cookie_file = tmp_path / "linkedin_state.json"
    cookie_file.write_text(json.dumps({
        "cookies": [{"name": "li_at", "value": "old"}], "origins": [],
    }))
    PlaywrightConnector()._save_storage_state(_FakeContext(), str(cookie_file))

    data = json.loads(cookie_file.read_text())
    assert [c["value"] for c in data["cookies"] if c["name"] == "li_at"] == ["abc"]


def test_save_storage_state_swallows_errors(tmp_path):
    """Lỗi ghi (context hỏng) không được raise ra ngoài — chỉ log warning."""
    class _BrokenContext:
        def storage_state(self, path: str):
            raise RuntimeError("boom")

    cookie_file = tmp_path / "broken_state.json"
    # Không raise là pass.
    PlaywrightConnector()._save_storage_state(_BrokenContext(), str(cookie_file))
    assert not cookie_file.exists()
