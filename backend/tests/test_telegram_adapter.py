"""Unit tests cho Telegram adapter: escape, split message, inline keyboard."""

import pytest

from app.channels.base import DeliveryMessage, MessageButton
from app.channels.telegram import (
    TelegramAdapter,
    build_inline_keyboard,
    render_message,
    split_message,
)


class FakeAPI:
    """Thay TelegramAPI — ghi lại call, không ra mạng."""

    def __init__(self):
        self.calls = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.calls.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})
        return {}


# --- render_message: escape ký tự đặc biệt ---

def test_render_escapes_special_chars():
    msg = DeliveryMessage(title="AI <b>hot</b> & new", body="x < y & z")
    out = render_message(msg)
    assert "&lt;b&gt;hot&lt;/b&gt; &amp; new" in out
    assert "x &lt; y &amp; z" in out
    # Tag format của chính adapter vẫn còn (title bold)
    assert out.startswith("<b>")


def test_render_includes_dashboard_link():
    msg = DeliveryMessage(title="T", body="B", url="http://localhost:5173/insights/abc")
    out = render_message(msg)
    assert '<a href="http://localhost:5173/insights/abc">' in out


# --- split_message ---

def test_split_short_message_untouched():
    assert split_message("hello", limit=100) == ["hello"]

def test_split_long_message_respects_limit_and_keeps_lines():
    lines = [f"dòng số {i} " + "x" * 80 for i in range(50)]
    text = "\n".join(lines)
    chunks = split_message(text, limit=500)
    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)
    # Không mất dòng nào
    joined = "\n".join(chunks)
    for line in lines:
        assert line in joined

def test_split_hard_cuts_single_oversized_line():
    text = "a" * 9000
    chunks = split_message(text, limit=4000)
    assert len(chunks) == 3
    assert "".join(chunks) == text


# --- build_inline_keyboard ---

def test_keyboard_none_when_no_buttons():
    assert build_inline_keyboard([]) is None

def test_keyboard_callback_and_url_buttons():
    kb = build_inline_keyboard(
        [
            MessageButton(text="💬 Hỏi về tin này", callback_data="ask:123"),
            MessageButton(text="Mở dashboard", url="http://localhost:5173"),
        ]
    )
    rows = kb["inline_keyboard"]
    assert rows[0][0] == {"text": "💬 Hỏi về tin này", "callback_data": "ask:123"}
    assert rows[1][0] == {"text": "Mở dashboard", "url": "http://localhost:5173"}


# --- TelegramAdapter.send ---

@pytest.mark.asyncio
async def test_send_splits_and_attaches_keyboard_on_last_part():
    api = FakeAPI()
    adapter = TelegramAdapter(api)
    msg = DeliveryMessage(
        title="Tin dài",
        body="\n".join("nội dung " + "y" * 100 for _ in range(80)),
        buttons=[MessageButton(text="💬 Hỏi", callback_data="ask:1")],
    )
    result = await adapter.send("42", msg)
    assert result.ok
    assert result.parts == len(api.calls) > 1
    # Keyboard chỉ nằm ở phần cuối
    assert all(c["reply_markup"] is None for c in api.calls[:-1])
    assert api.calls[-1]["reply_markup"] is not None

@pytest.mark.asyncio
async def test_send_returns_error_on_api_failure():
    class BrokenAPI(FakeAPI):
        async def send_message(self, chat_id, text, reply_markup=None):
            raise RuntimeError("Telegram sendMessage failed: chat not found")

    adapter = TelegramAdapter(BrokenAPI())
    result = await adapter.send("42", DeliveryMessage(title="T", body="B"))
    assert not result.ok
    assert "chat not found" in result.error
