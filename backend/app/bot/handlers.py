"""Subscription handlers — /start, /subscribe, /unsubscribe, /status.

Flow /subscribe stateless: lựa chọn role sống trong chính inline keyboard của
message (nút có prefix ✅), toggle bằng editMessageReplyMarkup — không cần bảng
session. Role lấy từ ALLOWED_ROLES (9 job-title roles, KHÔNG phải 13
target_roles của Source).
"""

import logging

from app.ai.prompts import ALLOWED_ROLES
from app.channels.telegram import TelegramAPI
from app.config import settings
from app.database import async_session_maker
from app.repositories.subscriber_repo import SubscriberRepository

logger = logging.getLogger(__name__)

SELECTED_PREFIX = "✅ "

START_TEXT = (
    "Chào bạn! Mình là bot <b>AI Impact Radar</b> — báo tin AI đã được phân tích, "
    "đúng role của bạn.\n\n"
    "Lệnh:\n"
    "/subscribe — chọn role để nhận tin (alert khẩn + bản tin sáng)\n"
    "/status — xem đăng ký hiện tại\n"
    "/unsubscribe — tạm ngừng nhận tin\n"
    "/reset — thoát phiên hỏi đáp theo tin (khi có chatbot)"
)


def build_role_keyboard(selected: set[str]) -> dict:
    """Keyboard đa chọn role; hàng cuối là Lưu/Đóng."""
    rows = []
    for idx, role in enumerate(ALLOWED_ROLES):
        mark = SELECTED_PREFIX if role in selected else ""
        rows.append([{"text": f"{mark}{role}", "callback_data": f"sub:t:{idx}"}])
    rows.append(
        [
            {"text": "💾 Lưu", "callback_data": "sub:save"},
            {"text": "✖️ Đóng", "callback_data": "sub:close"},
        ]
    )
    return {"inline_keyboard": rows}


def parse_selected_from_markup(markup: dict | None) -> set[str]:
    """Đọc các role đang được tick từ reply_markup hiện tại của message."""
    selected: set[str] = set()
    for row in (markup or {}).get("inline_keyboard", []):
        for btn in row:
            text = btn.get("text", "")
            if text.startswith(SELECTED_PREFIX):
                selected.add(text.removeprefix(SELECTED_PREFIX))
    return selected


class SubscriptionHandlers:
    """Xử lý lệnh + callback subscription; mỗi update một DB session."""

    def __init__(self, api: TelegramAPI) -> None:
        self._api = api

    async def handle_start(self, chat_id: int, display_name: str | None) -> None:
        async with async_session_maker() as session:
            await SubscriberRepository(session).ensure_exists(chat_id, display_name)
        await self._api.send_message(chat_id, START_TEXT)

    async def handle_subscribe(self, chat_id: int) -> None:
        async with async_session_maker() as session:
            sub = await SubscriberRepository(session).get(chat_id)
        current = set(sub.roles) if sub else set()
        await self._api.send_message(
            chat_id,
            "Chọn role bạn muốn nhận tin (bấm để chọn/bỏ), xong bấm 💾 Lưu:",
            reply_markup=build_role_keyboard(current),
        )

    async def handle_unsubscribe(self, chat_id: int) -> None:
        async with async_session_maker() as session:
            existed = await SubscriberRepository(session).deactivate(chat_id)
        if existed:
            await self._api.send_message(
                chat_id, "Đã tạm ngừng nhận tin. Dùng /subscribe khi muốn nhận lại."
            )
        else:
            await self._api.send_message(
                chat_id, "Bạn chưa đăng ký nhận tin. Dùng /subscribe để bắt đầu."
            )

    async def handle_status(self, chat_id: int) -> None:
        async with async_session_maker() as session:
            sub = await SubscriberRepository(session).get(chat_id)
        if sub is None or not sub.roles:
            text = "Bạn chưa đăng ký role nào. Dùng /subscribe để chọn."
        elif not sub.active:
            text = (
                f"Đang TẠM NGỪNG nhận tin. Role đã lưu: {', '.join(sub.roles)}.\n"
                "Dùng /subscribe để nhận lại."
            )
        else:
            text = f"Đang nhận tin cho role: {', '.join(sub.roles)}."
        await self._api.send_message(chat_id, text)

    async def handle_callback(
        self,
        callback_query_id: str,
        chat_id: int,
        message_id: int,
        data: str,
        current_markup: dict | None,
        display_name: str | None,
    ) -> None:
        """Callback `sub:*` — toggle role / lưu / đóng."""
        selected = parse_selected_from_markup(current_markup)

        if data.startswith("sub:t:"):
            try:
                role = ALLOWED_ROLES[int(data.removeprefix("sub:t:"))]
            except (ValueError, IndexError):
                await self._api.answer_callback_query(callback_query_id)
                return
            selected.symmetric_difference_update({role})
            await self._api.edit_message_reply_markup(
                chat_id, message_id, build_role_keyboard(selected)
            )
            await self._api.answer_callback_query(callback_query_id)

        elif data == "sub:save":
            roles = [r for r in ALLOWED_ROLES if r in selected]  # giữ thứ tự taxonomy
            async with async_session_maker() as session:
                await SubscriberRepository(session).set_roles(chat_id, roles, display_name)
            await self._api.answer_callback_query(callback_query_id, text="Đã lưu ✔")
            if roles:
                text = f"Đã đăng ký nhận tin cho role: {', '.join(roles)}."
            else:
                text = "Bạn không chọn role nào — sẽ không nhận tin. Dùng /subscribe để chọn lại."
            await self._api.send_message(chat_id, text)

        elif data == "sub:close":
            await self._api.answer_callback_query(callback_query_id)
            await self._api.edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": []})

        else:
            await self._api.answer_callback_query(callback_query_id)
