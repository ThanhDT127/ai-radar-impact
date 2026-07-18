"""Delivery Engine (M7) — rule-based push: alert critical + digest hằng ngày.

Rule v1 (D3): urgency=critical → alert trong ≤5 phút; còn lại → digest sáng.
Lookback window thay cho "mốc bật delivery"; delivery_log chống gửi trùng.
Format thuần template từ fields có sẵn — KHÔNG gọi Gemini ($0 AI).
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.base import ChannelAdapter, DeliveryMessage, MessageButton
from app.config import settings
from app.models.insight import Insight
from app.models.subscriber import Subscriber
from app.repositories.delivery_log_repo import DeliveryLogRepository
from app.repositories.insight_repo import InsightRepository
from app.repositories.subscriber_repo import SubscriberRepository

logger = logging.getLogger(__name__)

DIGEST_DISPLAY_CAP = 15

_URGENCY_EMOJI = {"critical": "🚨", "high": "🔴", "medium": "🟠", "low": "🟢"}


def roles_match(subscriber_roles: list[str], affected_roles: list[str] | None) -> bool:
    """Subscriber nhận insight khi giao role khác rỗng; 'Toàn công ty' → mọi người."""
    if not subscriber_roles:
        return False
    affected = affected_roles or []
    if "Toàn công ty" in affected:
        return True
    return bool(set(subscriber_roles) & set(affected))


def render_alert(insight: Insight, base_url: str) -> DeliveryMessage:
    body_parts = [p for p in [insight.signal, insight.why_it_matters] if p]
    return DeliveryMessage(
        title=f"🚨 {insight.title}",
        body="\n\n".join(body_parts),
        url=f"{base_url}/insights/{insight.id}",
        buttons=[MessageButton(text="💬 Hỏi về tin này", callback_data=f"ask:{insight.id}")],
    )


def render_alert_summary(insights: list[Insight], base_url: str) -> DeliveryMessage:
    """Tin tổng hợp khi vượt trần alert/giờ — 1 dòng/insight, không nút."""
    lines = [f"• {i.title}" for i in insights]
    return DeliveryMessage(
        title=f"🚨 {len(insights)} cảnh báo mới (gom do vượt trần alert/giờ)",
        body="\n".join(lines),
        url=base_url,
    )


def render_digest(insights: list[Insight], base_url: str) -> DeliveryMessage:
    """Digest nhóm theo topic đầu tiên, 1 dòng/insight, cap 15 hiển thị."""
    shown = insights[:DIGEST_DISPLAY_CAP]
    overflow = len(insights) - len(shown)

    by_topic: dict[str, list[Insight]] = {}
    for insight in shown:
        topic = insight.topics[0] if insight.topics else "Khác"
        by_topic.setdefault(topic, []).append(insight)

    lines: list[str] = []
    for topic, items in by_topic.items():
        lines.append(f"📌 {topic}")
        for i in items:
            emoji = _URGENCY_EMOJI.get(i.urgency or "", "⚪")
            lines.append(f"  {emoji} {i.title}")
        lines.append("")
    if overflow > 0:
        lines.append(f"+{overflow} tin khác — xem trên dashboard")

    return DeliveryMessage(
        title=f"📰 Bản tin AI Radar {datetime.now():%d/%m}",
        body="\n".join(lines).strip(),
        url=base_url,
    )


class DeliveryEngine:
    def __init__(self, session: AsyncSession, adapter: ChannelAdapter) -> None:
        self.insight_repo = InsightRepository(session)
        self.subscriber_repo = SubscriberRepository(session)
        self.log_repo = DeliveryLogRepository(session)
        self.adapter = adapter

    async def run_alert_cycle(self) -> dict[str, int]:
        """Quét insight critical trong lookback, gửi cho subscriber khớp role."""
        since = datetime.utcnow() - timedelta(hours=settings.delivery_alert_lookback_hours)
        insights = await self.insight_repo.list_for_delivery(since, critical=True)
        if not insights:
            return {"sent": 0, "skipped": 0}

        subscribers = await self.subscriber_repo.list_active()
        sent = skipped = 0
        for sub in subscribers:
            sent_count, skipped_count = await self._alert_subscriber(sub, insights)
            sent += sent_count
            skipped += skipped_count
        if sent:
            logger.info("[delivery] Alert cycle: sent=%d skipped=%d", sent, skipped)
        return {"sent": sent, "skipped": skipped}

    async def _alert_subscriber(
        self, sub: Subscriber, insights: list[Insight]
    ) -> tuple[int, int]:
        candidates = [i for i in insights if roles_match(sub.roles, i.affected_roles)]
        if not candidates:
            return 0, 0
        already = await self.log_repo.sent_insight_ids(
            sub.chat_id, "alert", [i.id for i in candidates]
        )
        todo = [i for i in candidates if i.id not in already]
        if not todo:
            return 0, len(candidates)

        recent = await self.log_repo.count_alerts_last_hour(sub.chat_id)
        if recent + len(todo) > settings.delivery_max_alerts_per_hour:
            # Bão alert → gom thành 1 tin tổng hợp thay vì gửi lẻ
            result = await self.adapter.send(
                str(sub.chat_id), render_alert_summary(todo, settings.dashboard_base_url)
            )
            if result.ok:
                await self.log_repo.log_sent([i.id for i in todo], sub.chat_id, "alert")
                return len(todo), len(already)
            return 0, len(already)

        sent = 0
        for insight in todo:
            result = await self.adapter.send(
                str(sub.chat_id), render_alert(insight, settings.dashboard_base_url)
            )
            # Chỉ log khi gửi OK — lỗi thì chu kỳ sau tự retry nhờ không có log
            if result.ok:
                await self.log_repo.log_sent([insight.id], sub.chat_id, "alert")
                sent += 1
        return sent, len(already)

    async def run_digest(self) -> dict[str, int]:
        """Gom insight không critical trong lookback thành 1 digest/subscriber."""
        since = datetime.utcnow() - timedelta(hours=settings.delivery_digest_lookback_hours)
        insights = await self.insight_repo.list_for_delivery(since, critical=False)
        subscribers = await self.subscriber_repo.list_active()

        digests_sent = 0
        for sub in subscribers:
            candidates = [i for i in insights if roles_match(sub.roles, i.affected_roles)]
            if not candidates:
                continue
            already = await self.log_repo.sent_insight_ids(
                sub.chat_id, "digest", [i.id for i in candidates]
            )
            todo = [i for i in candidates if i.id not in already]
            if not todo:
                continue  # không gửi digest rỗng

            result = await self.adapter.send(
                str(sub.chat_id), render_digest(todo, settings.dashboard_base_url)
            )
            if result.ok:
                # Log MỌI insight trong kỳ, kể cả phần "+N tin khác" —
                # digest là bản tin, không phải hàng đợi (không dồn sang hôm sau)
                await self.log_repo.log_sent([i.id for i in todo], sub.chat_id, "digest")
                digests_sent += 1

        logger.info("[delivery] Digest run: %d digest(s) sent", digests_sent)
        return {"digests": digests_sent}
