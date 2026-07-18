"""Telegram channel: API client mỏng + adapter render DeliveryMessage.

Dùng HTML parse mode (ít ký tự phải escape hơn MarkdownV2). Mọi nội dung động
đều đi qua html.escape trước khi ghép — DeliveryMessage mang plain text.
"""

import html
import logging

import httpx

from app.channels.base import ChannelAdapter, DeliveryMessage, MessageButton, SendResult

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
# Telegram giới hạn 4096 ký tự/message; chừa biên cho tag HTML bao ngoài.
MAX_MESSAGE_CHARS = 4000


class TelegramAPI:
    """Client mỏng cho Bot API — dùng chung cho adapter (gửi) và worker (nhận)."""

    def __init__(self, token: str, timeout: float = 65.0) -> None:
        self._base = f"{TELEGRAM_API_BASE}/bot{token}"
        self._client = httpx.AsyncClient(timeout=timeout)

    async def call(self, method: str, **params) -> dict:
        """Gọi 1 method Bot API; raise RuntimeError khi Telegram trả ok=false."""
        resp = await self._client.post(f"{self._base}/{method}", json=params)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method} failed: {data.get('description')}")
        return data["result"]

    async def send_message(self, chat_id: int | str, text: str, reply_markup: dict | None = None) -> dict:
        params: dict = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            params["reply_markup"] = reply_markup
        return await self.call("sendMessage", **params)

    async def get_updates(self, offset: int | None, timeout: int = 50) -> list[dict]:
        params: dict = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"],
        }
        if offset is not None:
            params["offset"] = offset
        return await self.call("getUpdates", **params)

    async def answer_callback_query(self, callback_query_id: str, text: str | None = None) -> None:
        params: dict = {"callback_query_id": callback_query_id}
        if text:
            params["text"] = text
        await self.call("answerCallbackQuery", **params)

    async def edit_message_reply_markup(self, chat_id: int, message_id: int, reply_markup: dict) -> None:
        await self.call(
            "editMessageReplyMarkup",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )

    async def close(self) -> None:
        await self._client.aclose()


def render_message(message: DeliveryMessage) -> str:
    """Render DeliveryMessage sang HTML Telegram, escape toàn bộ nội dung động."""
    parts = [f"<b>{html.escape(message.title)}</b>"]
    if message.body:
        parts.append(html.escape(message.body))
    if message.url:
        parts.append(f'<a href="{html.escape(message.url, quote=True)}">Xem trên dashboard</a>')
    return "\n\n".join(parts)


def split_message(text: str, limit: int = MAX_MESSAGE_CHARS) -> list[str]:
    """Chia text theo ranh giới dòng để mỗi phần ≤ limit (dòng quá dài thì cắt cứng)."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        # Dòng đơn lẻ vượt limit → cắt cứng theo limit
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def build_inline_keyboard(buttons: list[MessageButton]) -> dict | None:
    """Inline keyboard 1 nút/hàng; None nếu không có nút."""
    if not buttons:
        return None
    rows = []
    for b in buttons:
        btn: dict = {"text": b.text}
        if b.callback_data:
            btn["callback_data"] = b.callback_data
        elif b.url:
            btn["url"] = b.url
        rows.append([btn])
    return {"inline_keyboard": rows}


class TelegramAdapter(ChannelAdapter):
    """Adapter Telegram — implementation đầu tiên của ChannelAdapter."""

    channel_type = "telegram"

    def __init__(self, api: TelegramAPI) -> None:
        self._api = api

    async def send(self, recipient_ref: str, message: DeliveryMessage) -> SendResult:
        text = render_message(message)
        chunks = split_message(text)
        keyboard = build_inline_keyboard(message.buttons)
        try:
            for i, chunk in enumerate(chunks):
                # Keyboard gắn vào phần cuối để nút nằm dưới cùng nội dung
                markup = keyboard if i == len(chunks) - 1 else None
                await self._api.send_message(recipient_ref, chunk, reply_markup=markup)
            return SendResult(ok=True, parts=len(chunks))
        except (httpx.HTTPError, RuntimeError) as exc:
            logger.warning("Telegram send to %s failed: %s", recipient_ref, exc)
            return SendResult(ok=False, error=str(exc), parts=len(chunks))
