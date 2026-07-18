"""Router update Telegram → handler tương ứng.

Ranh giới với change `chatbot-qa`: transport (change này) nhận mọi update;
Q&A (callback `ask:`, text tự do, `/reset`) chuyển cho chat handler do
`chatbot-qa` đăng ký qua `register_chat_handler()`. Chưa đăng ký → trả lời tạm.
"""

import logging
from typing import Protocol

from app.bot.handlers import SubscriptionHandlers
from app.channels.telegram import TelegramAPI
from app.config import settings
from app.database import async_session_maker
from app.repositories.subscriber_repo import SubscriberRepository

logger = logging.getLogger(__name__)


class ChatQAHandler(Protocol):
    """Interface mà `chat-telegram-surface` (change chatbot-qa) sẽ implement."""

    async def handle_text(self, chat_id: int, text: str) -> None: ...
    async def handle_ask(self, chat_id: int, insight_id: str) -> None: ...
    async def handle_reset(self, chat_id: int) -> None: ...


class UpdateRouter:
    def __init__(self, api: TelegramAPI, subscriptions: SubscriptionHandlers) -> None:
        self._api = api
        self._subscriptions = subscriptions
        self._chat_handler: ChatQAHandler | None = None

    def register_chat_handler(self, handler: ChatQAHandler) -> None:
        self._chat_handler = handler
        logger.info("[bot] Chat Q&A handler registered: %s", type(handler).__name__)

    async def route(self, update: dict) -> None:
        if "callback_query" in update:
            await self._route_callback(update["callback_query"])
        elif "message" in update:
            await self._route_message(update["message"])

    async def _route_callback(self, cq: dict) -> None:
        data = cq.get("data", "")
        message = cq.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id is None:
            await self._api.answer_callback_query(cq["id"])
            return

        if data.startswith("sub:"):
            await self._subscriptions.handle_callback(
                callback_query_id=cq["id"],
                chat_id=chat_id,
                message_id=message.get("message_id"),
                data=data,
                current_markup=message.get("reply_markup"),
                display_name=_display_name(cq.get("from")),
            )
        elif data.startswith("ask:"):
            await self._api.answer_callback_query(cq["id"])
            insight_id = data.removeprefix("ask:")
            if self._chat_handler:
                await self._chat_handler.handle_ask(chat_id, insight_id)
            else:
                await self._api.send_message(
                    chat_id,
                    "Tính năng hỏi đáp đang được phát triển, sắp ra mắt 🙌\n"
                    f"Xem chi tiết tin này trên dashboard: "
                    f"{settings.dashboard_base_url}/insights/{insight_id}",
                )
        else:
            await self._api.answer_callback_query(cq["id"])

    async def _route_message(self, message: dict) -> None:
        text = message.get("text")
        chat_id = (message.get("chat") or {}).get("id")
        if not text or chat_id is None:
            return
        display_name = _display_name(message.get("from"))

        command = text.split()[0].split("@")[0].lower() if text.startswith("/") else None

        if command == "/start":
            await self._subscriptions.handle_start(chat_id, display_name)
        elif command == "/subscribe":
            await self._subscriptions.handle_subscribe(chat_id)
        elif command == "/unsubscribe":
            await self._subscriptions.handle_unsubscribe(chat_id)
        elif command == "/status":
            await self._subscriptions.handle_status(chat_id)
        elif command == "/reset":
            if self._chat_handler:
                await self._chat_handler.handle_reset(chat_id)
            else:
                await self._send_qa_placeholder(chat_id)
        elif command is not None:
            await self._api.send_message(
                chat_id, "Lệnh không hỗ trợ. Các lệnh: /subscribe, /status, /unsubscribe, /reset"
            )
        else:
            await self._route_free_text(chat_id, text)

    async def _route_free_text(self, chat_id: int, text: str) -> None:
        if self._chat_handler:
            await self._chat_handler.handle_text(chat_id, text)
            return
        # Chat lạ (chưa /start) → hướng dẫn bắt đầu thay vì placeholder Q&A
        async with async_session_maker() as session:
            known = await SubscriberRepository(session).get(chat_id)
        if known is None:
            await self._api.send_message(
                chat_id, "Chào bạn! Gửi /start để bắt đầu dùng bot AI Impact Radar."
            )
        else:
            await self._send_qa_placeholder(chat_id)

    async def _send_qa_placeholder(self, chat_id: int) -> None:
        await self._api.send_message(
            chat_id,
            "Tính năng hỏi đáp đang được phát triển, sắp ra mắt 🙌\n"
            f"Trong lúc chờ, xem insight trên dashboard: {settings.dashboard_base_url}",
        )


def _display_name(user: dict | None) -> str | None:
    if not user:
        return None
    name = " ".join(p for p in [user.get("first_name"), user.get("last_name")] if p)
    return name[:200] or None
