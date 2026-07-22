"""Unit tests cho DeliveryEngine: xếp hạng, trần số lượng, thứ tự, idempotency, render."""

import uuid
from datetime import datetime

import pytest

from app.channels.base import ChannelAdapter, DeliveryMessage, SendResult
from app.channels.email_templates import render_brief
from app.models.insight import Insight
from app.models.subscriber import Subscriber
from app.services.delivery_engine import (
    DELIVERY_KIND,
    DeliveryEngine,
    display_title,
    owning_role,
    role_urgency,
    roles_match,
    score_for_role,
    select_for_subscriber,
)


def make_insight(
    title="Tin test",
    roles=None,
    role_urgency="high",
    recommendations=None,
    impact_label="Trung bình",
    actionability_score=0.7,
    intelligence_tier="Tactical",
    trust_score=0.8,
    summary_short=None,
    **extra,
) -> Insight:
    """Insight test; `role_urgency` sinh sẵn recommendations cho mọi affected_role."""
    affected = roles if roles is not None else ["Dev"]
    if recommendations is None and role_urgency is not None:
        recommendations = {
            r: {"action_type": "read", "note": "Ghi chú.", "urgency": role_urgency}
            for r in affected
        }
    return Insight(
        id=uuid.uuid4(),
        title=title,
        summary_short=summary_short,
        affected_roles=affected,
        topics=["Trí tuệ nhân tạo"],
        signal="Signal test",
        so_what="Điều đáng nói",
        why_it_matters="Vì sao quan trọng",
        summary_medium="Tóm tắt dài hơn về tin này.",
        impact_label=impact_label,
        actionability_score=actionability_score,
        intelligence_tier=intelligence_tier,
        trust_score=trust_score,
        published_at=datetime(2026, 7, 20, 8, 0),
        created_at=datetime(2026, 7, 20, 8, 0),
        source_url="https://example.com/a",
        recommendations=recommendations,
        **extra,
    )


def make_sub(email="a@x.vn", roles=("Dev",), active=True) -> Subscriber:
    return Subscriber(
        id=uuid.uuid4(),
        email=email,
        roles=list(roles),
        active=active,
        unsubscribe_token=uuid.uuid4().hex,
    )


class FakeAdapter(ChannelAdapter):
    channel_type = "fake"

    def __init__(self, ok=True):
        self.sent: list[tuple[str, DeliveryMessage]] = []
        self.ok = ok
        self.opened = self.closed = 0

    async def open(self) -> None:
        self.opened += 1

    async def close(self) -> None:
        self.closed += 1

    async def send(self, recipient_ref: str, message: DeliveryMessage) -> SendResult:
        self.sent.append((recipient_ref, message))
        return SendResult(ok=self.ok, error=None if self.ok else "smtp lỗi")


class FakeInsightRepo:
    def __init__(self, insights):
        self._insights = insights

    async def list_for_delivery(self, since):
        return list(self._insights)


class FakeSubscriberRepo:
    def __init__(self, subs):
        self._subs = subs

    async def list_active(self):
        return [s for s in self._subs if s.active and s.roles]


class FakeLogRepo:
    def __init__(self):
        self.logged: set[tuple] = set()
        self.recent: set[tuple] = set()

    async def sent_insight_ids(self, subscriber_id, kind, insight_ids):
        return {i for i in insight_ids if (i, subscriber_id, kind) in self.logged}

    async def sent_within(self, subscriber_id, kind, hours):
        return (subscriber_id, kind) in self.recent

    async def log_sent(self, insight_ids, subscriber_id, kind):
        for i in insight_ids:
            self.logged.add((i, subscriber_id, kind))
        self.recent.add((subscriber_id, kind))


def make_engine(insights, subs, adapter=None):
    engine = DeliveryEngine.__new__(DeliveryEngine)
    engine.insight_repo = FakeInsightRepo(insights)
    engine.subscriber_repo = FakeSubscriberRepo(subs)
    engine.log_repo = FakeLogRepo()
    engine.adapter = adapter or FakeAdapter()
    return engine


# ── Xếp hạng ─────────────────────────────────────────────────────────────────


def test_role_urgency_defaults_to_medium_when_key_missing():
    """Insight cũ chưa có khoá urgency không bị đẩy lên đầu cũng không bị loại."""
    insight = make_insight(roles=["Dev"], recommendations={"Dev": {"action_type": "read"}})
    assert role_urgency(insight, "Dev") == "medium"


def test_role_urgency_ignores_value_outside_closed_set():
    insight = make_insight(roles=["Dev"], recommendations={"Dev": {"urgency": "critical"}})
    assert role_urgency(insight, "Dev") == "medium"


def test_high_urgency_outranks_higher_impact_label():
    """Urgency theo vai trò là tiêu chí số 1, đứng trên impact_label."""
    high = make_insight(roles=["Dev"], role_urgency="high", impact_label="Thấp")
    low = make_insight(roles=["Dev"], role_urgency="low", impact_label="Nghiêm trọng")
    assert score_for_role(high, "Dev") > score_for_role(low, "Dev")


def test_practical_indicator_breaks_tie():
    plain = make_insight(roles=["Dev"])
    patched = make_insight(roles=["Dev"], practical_indicators={"has_security_patch": True})
    assert score_for_role(patched, "Dev") > score_for_role(plain, "Dev")


# ── Chọn tin & trần số lượng ─────────────────────────────────────────────────


def test_caps_items_per_role():
    sub = make_sub(roles=["Security"])
    insights = [make_insight(title=f"Tin {n}", roles=["Security"]) for n in range(9)]
    sections, overflow = select_for_subscriber(sub, insights, max_per_role=2, max_per_email=3)
    assert [len(items) for _, items in sections] == [2]
    assert overflow == 7


def test_email_cap_applies_to_total_not_per_role():
    """Đăng ký 3 vai trò không có nghĩa nhận 2×3 tin."""
    sub = make_sub(roles=["Security", "AI Engineer", "Tech Lead"])
    insights = [
        make_insight(title=f"{role} {n}", roles=[role])
        for role in ("Security", "AI Engineer", "Tech Lead")
        for n in range(3)
    ]
    sections, _ = select_for_subscriber(sub, insights, max_per_role=2, max_per_email=3)
    assert sum(len(items) for _, items in sections) == 3


def test_subscriber_without_high_urgency_still_gets_items():
    """Vai trò không có tin `high` vẫn nhận tin tốt nhất trong số khớp (không bỏ đói)."""
    sub = make_sub(roles=["Data Scientist"])
    insights = [
        make_insight(title=f"Tin {n}", roles=["Data Scientist"], role_urgency="medium")
        for n in range(29)
    ]
    sections, overflow = select_for_subscriber(sub, insights, max_per_role=2, max_per_email=3)
    assert sum(len(items) for _, items in sections) == 2
    assert overflow == 27


def test_ordering_is_urgency_descending():
    """Section vai trò sắp theo tin đứng đầu; trong section sắp giảm dần."""
    sub = make_sub(roles=["Security", "AI Engineer"])
    sec_high = make_insight(title="Sec cao", roles=["Security"], role_urgency="high",
                            impact_label="Nghiêm trọng")
    sec_medium = make_insight(title="Sec vừa", roles=["Security"], role_urgency="medium")
    ai_high = make_insight(title="AI cao", roles=["AI Engineer"], role_urgency="high",
                           impact_label="Thấp")
    sections, _ = select_for_subscriber(
        sub, [sec_medium, ai_high, sec_high], max_per_role=2, max_per_email=3
    )
    assert [role for role, _ in sections] == ["Security", "AI Engineer"]
    assert [i.title for i in sections[0][1]] == ["Sec cao", "Sec vừa"]


def test_insight_matching_two_roles_appears_once():
    sub = make_sub(roles=["AI Engineer", "Tech Lead"])
    insight = make_insight(
        roles=["AI Engineer", "Tech Lead"],
        recommendations={
            "AI Engineer": {"action_type": "test", "note": "x", "urgency": "high"},
            "Tech Lead": {"action_type": "watch", "note": "y", "urgency": "low"},
        },
    )
    sections, _ = select_for_subscriber(sub, [insight], max_per_role=2, max_per_email=3)
    assert sum(len(items) for _, items in sections) == 1
    assert sections[0][0] == "AI Engineer"


def test_company_wide_insight_goes_to_its_own_section():
    sub = make_sub(roles=["Dev"])
    insight = make_insight(roles=["Toàn công ty"], recommendations={})
    assert roles_match(sub.roles, insight.affected_roles) is True
    assert owning_role(sub.roles, insight) == "Toàn công ty"


# ── Gửi & idempotency ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_brief_sends_one_email_per_subscriber():
    subs = [make_sub(email="a@x.vn", roles=["Dev"]), make_sub(email="b@x.vn", roles=["Security"])]
    insights = [make_insight(roles=["Dev"]), make_insight(roles=["Security"])]
    adapter = FakeAdapter()
    engine = make_engine(insights, subs, adapter)

    result = await engine.run_brief()

    assert result["sent"] == 2
    assert sorted(r for r, _ in adapter.sent) == ["a@x.vn", "b@x.vn"]
    assert adapter.opened == 1 and adapter.closed == 1


@pytest.mark.asyncio
async def test_second_run_sends_nothing():
    subs = [make_sub(roles=["Dev"])]
    engine = make_engine([make_insight(roles=["Dev"])], subs)

    first = await engine.run_brief()
    second = await engine.run_brief()

    assert first["sent"] == 1
    assert second["sent"] == 0


@pytest.mark.asyncio
async def test_capped_out_insight_is_not_logged_and_competes_next_run():
    """Tin bị loại vì trần KHÔNG ghi log — kỳ SAU còn cạnh tranh (cần qua chốt chu kỳ)."""
    subs = [make_sub(roles=["Dev"])]
    insights = [make_insight(title=f"Tin {n}", roles=["Dev"]) for n in range(6)]
    engine = make_engine(insights, subs)

    await engine.run_brief()
    assert len(engine.log_repo.logged) <= 3

    engine.log_repo.recent.clear()  # mô phỏng đã sang kỳ kế tiếp
    second = await engine.run_brief()
    assert second["sent"] == 1  # phần dư vẫn được gửi ở kỳ sau


@pytest.mark.asyncio
async def test_second_run_in_same_period_is_blocked_by_cadence_guard():
    """Chạy lại trong cùng kỳ KHÔNG được gửi tiếp lô tin kế tiếp.

    Unique constraint chỉ chặn gửi lại CÙNG MỘT TIN; lô kế tiếp là tin khác nên lọt qua.
    """
    subs = [make_sub(roles=["Dev"])]
    insights = [make_insight(title=f"Tin {n}", roles=["Dev"]) for n in range(20)]
    adapter = FakeAdapter()
    engine = make_engine(insights, subs, adapter)

    first = await engine.run_brief()
    second = await engine.run_brief()

    assert first["sent"] == 1
    assert second["sent"] == 0 and second["skipped"] == 1
    assert len(adapter.sent) == 1


@pytest.mark.asyncio
async def test_force_bypasses_cadence_guard():
    subs = [make_sub(roles=["Dev"])]
    insights = [make_insight(title=f"Tin {n}", roles=["Dev"]) for n in range(20)]
    engine = make_engine(insights, subs)

    await engine.run_brief()
    forced = await engine.run_brief(force=True)

    assert forced["sent"] == 1


@pytest.mark.asyncio
async def test_send_failure_is_not_logged():
    subs = [make_sub(roles=["Dev"])]
    engine = make_engine([make_insight(roles=["Dev"])], subs, FakeAdapter(ok=False))

    result = await engine.run_brief()

    assert result["failed"] == 1
    assert engine.log_repo.logged == set()


@pytest.mark.asyncio
async def test_no_matching_insight_sends_no_email():
    subs = [make_sub(roles=["Security"])]
    adapter = FakeAdapter()
    engine = make_engine([make_insight(roles=["Dev"])], subs, adapter)

    result = await engine.run_brief()

    assert result["sent"] == 0 and adapter.sent == []


@pytest.mark.asyncio
async def test_dry_run_does_not_send_or_log(capsys):
    subs = [make_sub(roles=["Dev"])]
    adapter = FakeAdapter()
    engine = make_engine([make_insight(roles=["Dev"])], subs, adapter)

    await engine.run_brief(dry_run=True)

    assert adapter.sent == [] and engine.log_repo.logged == set()
    assert adapter.opened == 0
    assert "SUBJECT:" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_message_carries_unsubscribe_headers():
    sub = make_sub(roles=["Dev"])
    adapter = FakeAdapter()
    engine = make_engine([make_insight(roles=["Dev"])], [sub], adapter)

    await engine.run_brief()

    _, message = adapter.sent[0]
    assert sub.unsubscribe_token in message.headers["List-Unsubscribe"]
    assert message.headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert message.html_body


# ── Render ───────────────────────────────────────────────────────────────────


def test_display_title_prefers_vietnamese_summary():
    insight = make_insight(title="Microsoft Patches 570 Flaws", summary_short="Microsoft vá 570 lỗ hổng")
    assert display_title(insight) == "Microsoft vá 570 lỗ hổng"


def test_display_title_keeps_vietnamese_title():
    insight = make_insight(title="Việt Nam ra mắt nền tảng AI", summary_short="Bản tóm tắt")
    assert display_title(insight) == "Việt Nam ra mắt nền tảng AI"


def test_long_title_is_not_truncated_in_body():
    long_title = "Tiêu đề rất dài " * 12
    insight = make_insight(title=long_title)
    subject, text, html = render_brief(
        [("Dev", [insight])], {insight.id: long_title.strip()}, 0, "http://d", "http://u"
    )
    assert long_title.strip() in text
    assert len(subject) <= 110


def test_missing_optional_fields_render_no_empty_labels():
    insight = make_insight(roles=["Dev"])
    insight.so_what = None
    insight.risks = None
    _, text, html = render_brief(
        [("Dev", [insight])], {insight.id: "Tiêu đề"}, 0, "http://d", "http://u"
    )
    assert "Điều đáng nói" not in text and "Rủi ro" not in text
    assert "Điều đáng nói" not in html


def test_text_body_is_readable_standalone():
    insight = make_insight(roles=["Dev"])
    _, text, _ = render_brief(
        [("Dev", [insight])], {insight.id: "Tiêu đề tin"}, 5, "http://d", "http://u"
    )
    assert "Tiêu đề tin" in text
    assert "Tóm tắt:" in text
    assert "http://d/insights/" in text
    assert "+5 tin khác" in text
    assert "Hủy nhận: http://u" in text


def test_subject_counts_only_items_in_this_email():
    """Đuôi subject đếm tin trong email, KHÔNG cộng overflow (tránh '+146 tin khác')."""
    top = make_insight(title="Tin đầu")
    second = make_insight(title="Tin hai")
    subject, _, _ = render_brief(
        [("Dev", [top, second])], {top.id: "Tin đầu", second.id: "Tin hai"}, 144, "http://d", "http://u"
    )
    assert "Tin đầu" in subject
    assert "+1 tin khác" in subject
    assert "144" not in subject


def test_recommendation_rendered_for_section_role_only():
    insight = make_insight(
        roles=["AI Engineer", "Dev"],
        recommendations={
            "AI Engineer": {"action_type": "test", "note": "Thử ngay.", "urgency": "high"},
            "Dev": {"action_type": "watch", "note": "Chỉ theo dõi.", "urgency": "low"},
        },
    )
    _, text, _ = render_brief(
        [("AI Engineer", [insight])], {insight.id: "Tiêu đề"}, 0, "http://d", "http://u"
    )
    assert "Thử ngay." in text
    assert "Chỉ theo dõi." not in text
