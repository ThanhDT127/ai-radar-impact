"""Unit tests cho UpdateRouter: routing lệnh, callback ask:, chế độ chưa có chatbot."""

import pytest

from app.bot.router import UpdateRouter
from app.config import settings


class FakeAPI:
    def __init__(self):
        self.messages = []
        self.answered = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.messages.append({"chat_id": chat_id, "text": text})
        return {}

    async def answer_callback_query(self, callback_query_id, text=None):
        self.answered.append(callback_query_id)


class FakeSubscriptions:
    def __init__(self):
        self.calls = []

    async def handle_start(self, chat_id, display_name):
        self.calls.append(("start", chat_id))

    async def handle_subscribe(self, chat_id):
        self.calls.append(("subscribe", chat_id))

    async def handle_unsubscribe(self, chat_id):
        self.calls.append(("unsubscribe", chat_id))

    async def handle_status(self, chat_id):
        self.calls.append(("status", chat_id))

    async def handle_callback(self, **kwargs):
        self.calls.append(("callback", kwargs["data"]))


class FakeChatHandler:
    def __init__(self):
        self.calls = []

    async def handle_text(self, chat_id, text):
        self.calls.append(("text", chat_id, text))

    async def handle_ask(self, chat_id, insight_id):
        self.calls.append(("ask", chat_id, insight_id))

    async def handle_reset(self, chat_id):
        self.calls.append(("reset", chat_id))


def make_router():
    api = FakeAPI()
    subs = FakeSubscriptions()
    return UpdateRouter(api, subs), api, subs


def msg_update(text, chat_id=10):
    return {"message": {"text": text, "chat": {"id": chat_id}, "from": {"first_name": "Test"}}}


def callback_update(data, chat_id=10):
    return {
        "callback_query": {
            "id": "cq1",
            "data": data,
            "from": {"first_name": "Test"},
            "message": {"message_id": 5, "chat": {"id": chat_id}},
        }
    }


@pytest.mark.asyncio
async def test_commands_route_to_subscription_handlers():
    router, _, subs = make_router()
    for cmd in ["/start", "/subscribe", "/unsubscribe", "/status"]:
        await router.route(msg_update(cmd))
    assert [c[0] for c in subs.calls] == ["start", "subscribe", "unsubscribe", "status"]


@pytest.mark.asyncio
async def test_command_with_botname_suffix_still_routes():
    router, _, subs = make_router()
    await router.route(msg_update("/subscribe@my_radar_bot"))
    assert subs.calls == [("subscribe", 10)]


@pytest.mark.asyncio
async def test_sub_callback_routes_to_subscription():
    router, api, subs = make_router()
    await router.route(callback_update("sub:t:2"))
    assert subs.calls == [("callback", "sub:t:2")]


@pytest.mark.asyncio
async def test_ask_callback_without_chat_handler_sends_placeholder_with_link():
    router, api, _ = make_router()
    await router.route(callback_update("ask:abc-123"))
    assert api.answered == ["cq1"]  # spinner luôn được clear
    assert len(api.messages) == 1
    assert f"{settings.dashboard_base_url}/insights/abc-123" in api.messages[0]["text"]


@pytest.mark.asyncio
async def test_reset_without_chat_handler_sends_placeholder():
    router, api, _ = make_router()
    await router.route(msg_update("/reset"))
    assert "sắp ra mắt" in api.messages[0]["text"]


@pytest.mark.asyncio
async def test_registered_chat_handler_receives_ask_reset_and_text():
    router, api, _ = make_router()
    handler = FakeChatHandler()
    router.register_chat_handler(handler)

    await router.route(callback_update("ask:xyz"))
    await router.route(msg_update("/reset"))
    await router.route(msg_update("tuần này có gì mới?"))

    assert handler.calls == [
        ("ask", 10, "xyz"),
        ("reset", 10),
        ("text", 10, "tuần này có gì mới?"),
    ]
    assert api.messages == []  # không có placeholder nào khi handler đã đăng ký


@pytest.mark.asyncio
async def test_unknown_command_gets_help_reply():
    router, api, _ = make_router()
    await router.route(msg_update("/foobar"))
    assert "Lệnh không hỗ trợ" in api.messages[0]["text"]
