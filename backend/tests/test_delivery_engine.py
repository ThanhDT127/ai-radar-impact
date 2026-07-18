"""Unit tests cho DeliveryEngine: recipient matching, render, idempotency, bão alert."""

import uuid

import pytest

from app.channels.base import ChannelAdapter, DeliveryMessage, SendResult
from app.config import settings
from app.models.insight import Insight
from app.models.subscriber import Subscriber
from app.services.delivery_engine import (
    DIGEST_DISPLAY_CAP,
    DeliveryEngine,
    render_alert,
    render_digest,
    roles_match,
)


def make_insight(title="Tin test", urgency="critical", roles=None, topics=None) -> Insight:
    return Insight(
        id=uuid.uuid4(),
        title=title,
        urgency=urgency,
        affected_roles=roles if roles is not None else ["Dev"],
        topics=topics if topics is not None else ["Trí tuệ nhân tạo"],
        signal="Signal test",
        why_it_matters="Vì sao quan trọng",
        source_url="https://example.com/a",
    )


class FakeAdapter(ChannelAdapter):
    channel_type = "fake"

    def __init__(self):
        self.sent: list[tuple[str, DeliveryMessage]] = []

    async def send(self, recipient_ref: str, message: DeliveryMessage) -> SendResult:
        self.sent.append((recipient_ref, message))
        return SendResult(ok=True)


class FakeInsightRepo:
    def __init__(self, insights):
        self._insights = insights

    async def list_for_delivery(self, since, critical):
        if critical:
            return [i for i in self._insights if i.urgency == "critical"]
        return [i for i in self._insights if i.urgency != "critical"]


class FakeSubscriberRepo:
    def __init__(self, subs):
        self._subs = subs

    async def list_active(self):
        return [s for s in self._subs if s.active and s.roles]


class FakeLogRepo:
    def __init__(self):
        self.logged: set[tuple] = set()

    async def sent_insight_ids(self, chat_id, kind, insight_ids):
        return {i for i in insight_ids if (i, chat_id, kind) in self.logged}

    async def count_alerts_last_hour(self, chat_id):
        return sum(1 for (_, c, k) in self.logged if c == chat_id and k == "alert")

    async def log_sent(self, insight_ids, chat_id, kind):
        self.logged.update((i, chat_id, kind) for i in insight_ids)


def make_engine(insights, subs) -> tuple[DeliveryEngine, FakeAdapter, FakeLogRepo]:
    adapter = FakeAdapter()
    engine = DeliveryEngine(session=None, adapter=adapter)
    engine.insight_repo = FakeInsightRepo(insights)
    engine.subscriber_repo = FakeSubscriberRepo(subs)
    engine.log_repo = FakeLogRepo()
    return engine, adapter, engine.log_repo


# --- roles_match ---

def test_roles_match_partial_overlap():
    assert roles_match(["Security"], ["Dev", "Security"])

def test_roles_match_toan_cong_ty_reaches_everyone():
    assert roles_match(["Data Analyst"], ["Toàn công ty"])

def test_roles_match_no_overlap():
    assert not roles_match(["Data Analyst"], ["Dev"])

def test_roles_match_empty_subscriber_roles():
    assert not roles_match([], ["Toàn công ty"])


# --- render templates ---

def test_render_alert_has_signal_link_and_ask_button():
    insight = make_insight()
    msg = render_alert(insight, "http://localhost:5173")
    assert msg.title.startswith("🚨")
    assert "Signal test" in msg.body and "Vì sao quan trọng" in msg.body
    assert msg.url == f"http://localhost:5173/insights/{insight.id}"
    assert msg.buttons[0].callback_data == f"ask:{insight.id}"

def test_render_digest_caps_display_and_notes_overflow():
    insights = [make_insight(title=f"Tin {i}", urgency="medium") for i in range(22)]
    msg = render_digest(insights, "http://localhost:5173")
    shown = sum(1 for i in range(22) if f"Tin {i}" in msg.body)
    assert shown == DIGEST_DISPLAY_CAP
    assert "+7 tin khác" in msg.body

def test_render_digest_groups_by_topic():
    insights = [
        make_insight(title="Tin AI", urgency="low", topics=["Trí tuệ nhân tạo"]),
        make_insight(title="Tin bảo mật", urgency="high", topics=["An ninh mạng"]),
    ]
    msg = render_digest(insights, "http://localhost:5173")
    assert "📌 Trí tuệ nhân tạo" in msg.body
    assert "📌 An ninh mạng" in msg.body


# --- alert cycle ---

@pytest.mark.asyncio
async def test_alert_sent_once_then_idempotent():
    insight = make_insight(roles=["Dev"])
    sub = Subscriber(chat_id=1, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine([insight], [sub])

    first = await engine.run_alert_cycle()
    second = await engine.run_alert_cycle()
    assert first["sent"] == 1
    assert second["sent"] == 0
    assert len(adapter.sent) == 1

@pytest.mark.asyncio
async def test_alert_skips_non_matching_role():
    insight = make_insight(roles=["Security"])
    sub = Subscriber(chat_id=1, roles=["Data Analyst"], active=True)
    engine, adapter, _ = make_engine([insight], [sub])

    result = await engine.run_alert_cycle()
    assert result["sent"] == 0
    assert adapter.sent == []

@pytest.mark.asyncio
async def test_alert_storm_aggregated_into_single_message():
    count = settings.delivery_max_alerts_per_hour + 3
    insights = [make_insight(title=f"Bão {i}") for i in range(count)]
    sub = Subscriber(chat_id=1, roles=["Dev"], active=True)
    engine, adapter, log_repo = make_engine(insights, [sub])

    result = await engine.run_alert_cycle()
    # 1 tin tổng hợp thay vì N tin lẻ; tất cả đều được log
    assert len(adapter.sent) == 1
    assert "cảnh báo mới" in adapter.sent[0][1].title
    assert result["sent"] == count
    assert len(log_repo.logged) == count


# --- digest ---

@pytest.mark.asyncio
async def test_digest_sent_and_logs_all_including_overflow():
    insights = [make_insight(title=f"Tin {i}", urgency="medium") for i in range(20)]
    sub = Subscriber(chat_id=7, roles=["Dev"], active=True)
    engine, adapter, log_repo = make_engine(insights, [sub])

    result = await engine.run_digest()
    assert result["digests"] == 1
    # Log MỌI insight khớp, kể cả 5 tin "+N tin khác" không hiển thị
    assert len(log_repo.logged) == 20

@pytest.mark.asyncio
async def test_digest_not_sent_when_nothing_new():
    insights = [make_insight(urgency="medium")]
    sub = Subscriber(chat_id=7, roles=["Dev"], active=True)
    engine, adapter, log_repo = make_engine(insights, [sub])

    await engine.run_digest()
    second = await engine.run_digest()
    assert second["digests"] == 0
    assert len(adapter.sent) == 1  # chỉ lần đầu

@pytest.mark.asyncio
async def test_digest_excludes_critical():
    insights = [make_insight(urgency="critical")]
    sub = Subscriber(chat_id=7, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine(insights, [sub])

    result = await engine.run_digest()
    assert result["digests"] == 0
