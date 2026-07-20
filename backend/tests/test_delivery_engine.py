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
    display_title,
    render_alert,
    render_alert_summary,
    render_digest,
    roles_match,
)


def make_insight(
    title="Tin test",
    urgency="critical",
    roles=None,
    topics=None,
    role_urgency="high",
    recommendations=None,
) -> Insight:
    """Insight test.

    `role_urgency` là đường tắt: sinh `recommendations` với urgency đó cho mọi role
    trong `affected_roles` — đây mới là thứ quyết định alert. Truyền
    `recommendations=...` để dựng ca phức tạp, hoặc `role_urgency=None` để mô phỏng
    insight cũ (chưa có khoá `urgency`).
    """
    affected = roles if roles is not None else ["Dev"]
    if recommendations is None and role_urgency is not None:
        recommendations = {
            r: {"action_type": "read", "note": "Ghi chú.", "urgency": role_urgency}
            for r in affected
        }
    return Insight(
        id=uuid.uuid4(),
        title=title,
        urgency=urgency,
        affected_roles=affected,
        topics=topics if topics is not None else ["Trí tuệ nhân tạo"],
        signal="Signal test",
        why_it_matters="Vì sao quan trọng",
        source_url="https://example.com/a",
        recommendations=recommendations,
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

    async def list_for_delivery(self, since):
        # Repo không còn phân hoạch alert/digest — service lọc theo vai trò.
        return list(self._insights)


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
    # 🔴 (mức `high`) thay cho 🚨 — alert nay nghĩa là "đáng đọc ngay", không phải "khẩn cấp"
    assert msg.title.startswith("🔴")
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
async def test_alert_only_to_role_scored_high():
    """Cùng một tin: vai trò `high` nhận alert, vai trò `medium` không."""
    insight = make_insight(
        roles=["Security", "Dev"],
        recommendations={
            "Security": {"action_type": "read", "note": "n", "urgency": "high"},
            "Dev": {"action_type": "read", "note": "n", "urgency": "medium"},
        },
    )
    sec = Subscriber(chat_id=1, roles=["Security"], active=True)
    dev = Subscriber(chat_id=2, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine([insight], [sec, dev])

    result = await engine.run_alert_cycle()
    assert result["sent"] == 1
    assert [r for r, _ in adapter.sent] == ["1"]


@pytest.mark.asyncio
async def test_alert_for_non_security_event():
    """Tin `Phát hành mới` (urgency toàn cục không critical) vẫn alert được cho AI Engineer.

    Đây là ca "gửi thiếu" mà chuỗi cũ vĩnh viễn không tạo ra được.
    """
    insight = make_insight(urgency="medium", roles=["AI Engineer"], role_urgency="high")
    sub = Subscriber(chat_id=3, roles=["AI Engineer"], active=True)
    engine, adapter, _ = make_engine([insight], [sub])

    result = await engine.run_alert_cycle()
    assert result["sent"] == 1


@pytest.mark.asyncio
async def test_no_alert_when_role_absent_from_recommendations():
    """Có trong affected_roles nhưng vắng trong recommendations ⇒ không đủ tín hiệu."""
    insight = make_insight(
        roles=["Dev", "Security"],
        recommendations={
            "Security": {"action_type": "read", "note": "n", "urgency": "high"}
        },
    )
    sub = Subscriber(chat_id=4, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine([insight], [sub])

    result = await engine.run_alert_cycle()
    assert result["sent"] == 0
    assert adapter.sent == []


@pytest.mark.asyncio
async def test_legacy_insight_without_urgency_key_alerts_nobody():
    """Insight cũ (recommendations không có khoá `urgency`) không alert hồi tố."""
    insight = make_insight(
        roles=["Dev"],
        recommendations={"Dev": {"action_type": "read", "note": "n"}},
    )
    sub = Subscriber(chat_id=5, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine([insight], [sub])

    result = await engine.run_alert_cycle()
    assert result["sent"] == 0


@pytest.mark.asyncio
async def test_legacy_insight_with_null_recommendations_alerts_nobody():
    insight = make_insight(roles=["Dev"], role_urgency=None)
    sub = Subscriber(chat_id=6, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine([insight], [sub])

    assert (await engine.run_alert_cycle())["sent"] == 0


@pytest.mark.asyncio
async def test_alerted_insight_still_digests_to_other_role():
    """Tin alert cho Security vẫn là tin digest của người chỉ đăng ký Dev (task 3.3)."""
    insight = make_insight(
        roles=["Security", "Dev"],
        recommendations={
            "Security": {"action_type": "read", "note": "n", "urgency": "high"},
            "Dev": {"action_type": "read", "note": "n", "urgency": "low"},
        },
    )
    dev = Subscriber(chat_id=8, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine([insight], [dev])

    assert (await engine.run_alert_cycle())["sent"] == 0
    assert (await engine.run_digest())["digests"] == 1


@pytest.mark.asyncio
async def test_digest_skips_insight_already_alerted_under_old_rule():
    """Insight cũ từng alert theo luật `critical` không được nhắc lại trong digest.

    Nó không có role urgency nên `alert_roles_match` = False ⇒ lọt vào digest nếu chỉ
    dựa vào bộ lọc vai trò; chặn bằng delivery_log kind='alert'.
    """
    insight = make_insight(urgency="critical", roles=["Dev"], role_urgency=None)
    sub = Subscriber(chat_id=9, roles=["Dev"], active=True)
    engine, adapter, log_repo = make_engine([insight], [sub])
    log_repo.logged.add((insight.id, 9, "alert"))  # đã alert từ trước

    assert (await engine.run_digest())["digests"] == 0
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
    assert "tin đáng đọc ngay" in adapter.sent[0][1].title
    assert result["sent"] == count
    assert len(log_repo.logged) == count


# --- digest ---

@pytest.mark.asyncio
async def test_digest_sent_and_logs_all_including_overflow():
    insights = [
        make_insight(title=f"Tin {i}", urgency="medium", role_urgency="medium")
        for i in range(20)
    ]
    sub = Subscriber(chat_id=7, roles=["Dev"], active=True)
    engine, adapter, log_repo = make_engine(insights, [sub])

    result = await engine.run_digest()
    assert result["digests"] == 1
    # Log MỌI insight khớp, kể cả 5 tin "+N tin khác" không hiển thị
    assert len(log_repo.logged) == 20

@pytest.mark.asyncio
async def test_digest_not_sent_when_nothing_new():
    insights = [make_insight(urgency="medium", role_urgency="medium")]
    sub = Subscriber(chat_id=7, roles=["Dev"], active=True)
    engine, adapter, log_repo = make_engine(insights, [sub])

    await engine.run_digest()
    second = await engine.run_digest()
    assert second["digests"] == 0
    assert len(adapter.sent) == 1  # chỉ lần đầu

@pytest.mark.asyncio
async def test_digest_excludes_insight_alerted_to_this_subscriber():
    """Không gửi trùng: tin đã đủ điều kiện alert cho chính người này thì không vào digest.

    Thay cho test cũ `test_digest_excludes_critical` — cột vô hướng `urgency` không còn
    quyết định alert/digest nữa.
    """
    insights = [make_insight(urgency="critical", roles=["Dev"], role_urgency="high")]
    sub = Subscriber(chat_id=7, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine(insights, [sub])

    result = await engine.run_digest()
    assert result["digests"] == 0


@pytest.mark.asyncio
async def test_digest_includes_critical_insight_when_role_not_high():
    """Ngược lại: `urgency=critical` toàn cục KHÔNG còn tự động loại tin khỏi digest.

    Vai trò của người nhận chỉ ở mức `medium` ⇒ không alert ⇒ tin phải vào digest.
    """
    insights = [make_insight(urgency="critical", roles=["Dev"], role_urgency="medium")]
    sub = Subscriber(chat_id=7, roles=["Dev"], active=True)
    engine, adapter, _ = make_engine(insights, [sub])

    result = await engine.run_digest()
    assert result["digests"] == 1


# --- Tiêu đề tiếng Việt, khớp dashboard --------------------------------------


def _titled(title, summary_short):
    i = make_insight()
    i.title = title
    i.summary_short = summary_short
    return i


def test_display_title_uses_summary_when_title_is_english():
    """Title gốc tiếng Anh ⇒ dùng summary_short tiếng Việt (như dashboard)."""
    i = _titled(
        "Microsoft Patches a Record 570 Security Flaws",
        "Microsoft vá kỷ lục 570 lỗ hổng bảo mật trong bản cập nhật tháng này.",
    )
    assert display_title(i) == (
        "Microsoft vá kỷ lục 570 lỗ hổng bảo mật trong bản cập nhật tháng này."
    )


def test_display_title_keeps_title_when_already_vietnamese():
    i = _titled("Việt Nam ra mắt nền tảng AI mới", "Tóm tắt gì đó.")
    assert display_title(i) == "Việt Nam ra mắt nền tảng AI mới"


def test_display_title_falls_back_to_title_without_summary():
    i = _titled("OWASP/Nettacker", None)
    assert display_title(i) == "OWASP/Nettacker"


def test_display_title_handles_missing_title():
    i = _titled(None, None)
    assert display_title(i) == "Chưa có tiêu đề"


def test_alert_message_title_is_vietnamese():
    i = _titled("PyTorch 2.6 released", "PyTorch 2.6 ra mắt với tối ưu hiệu năng.")
    msg = render_alert(i, "https://x.test")
    assert msg.title == "🔴 PyTorch 2.6 ra mắt với tối ưu hiệu năng."


def test_digest_body_uses_vietnamese_titles():
    i = _titled("Google pays $250K bounty", "Google chi 250 nghìn đô tiền thưởng lỗi.")
    body = render_digest([i], "https://x.test").body
    assert "Google chi 250 nghìn đô tiền thưởng lỗi." in body
    assert "Google pays $250K bounty" not in body


def test_alert_summary_uses_vietnamese_titles_and_wording():
    i = _titled("Some English Headline", "Một tiêu đề tiếng Việt.")
    msg = render_alert_summary([i, i], "https://x.test")
    assert "Một tiêu đề tiếng Việt." in msg.body
    assert "Some English Headline" not in msg.body
    assert "đáng đọc ngay" in msg.title  # không còn gọi là "cảnh báo"


def test_shorten_keeps_short_text_intact():
    from app.services.delivery_engine import shorten
    assert shorten("Tin ngắn") == "Tin ngắn"


def test_shorten_cuts_at_word_boundary():
    from app.services.delivery_engine import shorten
    out = shorten("a" * 40 + " " + "b" * 200, limit=60)
    assert out.endswith("…")
    assert len(out) <= 61
    assert "b" * 200 not in out


def test_digest_line_is_truncated_but_alert_is_not():
    long_vi = "Kho GitHub nào đó đang trending, " + "mô tả rất dài " * 20
    i = _titled("English Repo Name", long_vi)
    digest_body = render_digest([i], "https://x.test").body
    assert "…" in digest_body
    # alert giữ nguyên, không cắt
    assert render_alert(i, "https://x.test").title == f"🔴 {long_vi.strip()}"
