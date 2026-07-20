"""Delivery Engine (M7) — rule-based push: alert theo vai trò + digest hằng ngày.

Rule v2 (change `role-aware-alert`): `recommendations[role].urgency == "high"` cho đúng vai
trò người nhận → alert trong ≤5 phút; còn lại → digest sáng.
Lookback window thay cho "mốc bật delivery"; delivery_log chống gửi trùng.
Format thuần template từ fields có sẵn — KHÔNG gọi Gemini ($0 AI).

Mọi text gửi đi phải là tiếng Việt, khớp dashboard — xem `display_title()`.
"""

import logging
import re
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

# Ngưỡng alert: chỉ `high` mới bắn alert; medium/low rơi vào digest (design D3).
ALERT_URGENCY_THRESHOLD = "high"

# Dấu tiếng Việt — dùng để nhận biết title đã là tiếng Việt hay còn nguyên bản tiếng Anh.
# Giữ ĐỒNG BỘ với `hasVietnamese` trong `frontend/src/components/InsightCard.tsx`.
_VIETNAMESE_CHARS = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)


def has_vietnamese(text: str | None) -> bool:
    return bool(text) and bool(_VIETNAMESE_CHARS.search(text))


DIGEST_TITLE_MAX = 110


def shorten(text: str, limit: int = DIGEST_TITLE_MAX) -> str:
    """Cắt ở ranh giới từ cho digest — 1 dòng/tin phải quét nhanh được.

    Cần vì `display_title` có thể trả `summary_short` (tới ~200 ký tự), dài hơn hẳn
    tiêu đề gốc. Alert không cắt: chỉ có 1 tin nên đọc đầy đủ được.
    """
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:–-")
    return f"{cut}…"


def display_title(insight: Insight) -> str:
    """Tiêu đề tiếng Việt để hiển thị — CÙNG luật với dashboard.

    `insights.title` là tiêu đề gốc của bài (phần lớn nguồn là tiếng Anh), còn
    `summary_short` do Gemini viết bằng tiếng Việt. Dashboard
    (`InsightCard.tsx::makeDisplayTitle`) vì thế ưu tiên `summary_short` khi title
    không có dấu tiếng Việt. Delivery phải theo đúng luật đó, nếu không cùng một tin
    sẽ hiện hai tiêu đề khác nhau ở hai nơi.
    """
    if insight.summary_short and not has_vietnamese(insight.title):
        return insight.summary_short.strip()
    return (insight.title or "Chưa có tiêu đề").strip()


def roles_match(subscriber_roles: list[str], affected_roles: list[str] | None) -> bool:
    """Subscriber nhận insight khi giao role khác rỗng; 'Toàn công ty' → mọi người.

    Đây là điều kiện của DIGEST. Alert dùng `alert_roles_match` — hẹp hơn.
    """
    if not subscriber_roles:
        return False
    affected = affected_roles or []
    if "Toàn công ty" in affected:
        return True
    return bool(set(subscriber_roles) & set(affected))


def matched_alert_roles(subscriber_roles: list[str], insight: Insight) -> list[str]:
    """Các vai trò của subscriber được chấm `high` cho tin này — dùng để log lý do gửi."""
    recs = insight.recommendations or {}
    if not isinstance(recs, dict):
        return []
    return [
        role
        for role in subscriber_roles or []
        if isinstance(recs.get(role), dict)
        and recs[role].get("urgency") == ALERT_URGENCY_THRESHOLD
    ]


def alert_roles_match(subscriber_roles: list[str], insight: Insight) -> bool:
    """True khi ≥1 vai trò của subscriber được chấm `urgency = "high"` cho tin này.

    Đọc `insights.recommendations[role].urgency` — mức ảnh hưởng tới RIÊNG vai trò đó,
    KHÔNG phải cột vô hướng `insights.urgency`.

    Vai trò có trong `affected_roles` nhưng vắng trong `recommendations` ⇒ không đủ tín
    hiệu ⇒ không alert (rơi về digest). Insight cũ chưa có khoá `urgency` cũng rơi vào
    nhánh này nên không alert hồi tố.
    """
    if not subscriber_roles:
        return False
    recs = insight.recommendations or {}
    if not isinstance(recs, dict):
        return False
    for role in subscriber_roles:
        entry = recs.get(role)
        if isinstance(entry, dict) and entry.get("urgency") == ALERT_URGENCY_THRESHOLD:
            return True
    return False


def render_alert(insight: Insight, base_url: str) -> DeliveryMessage:
    body_parts = [p for p in [insight.signal, insight.why_it_matters] if p]
    return DeliveryMessage(
        title=f"🔴 {display_title(insight)}",
        body="\n\n".join(body_parts),
        url=f"{base_url}/insights/{insight.id}",
        buttons=[MessageButton(text="💬 Hỏi về tin này", callback_data=f"ask:{insight.id}")],
    )


def render_alert_summary(insights: list[Insight], base_url: str) -> DeliveryMessage:
    """Tin tổng hợp khi vượt trần alert/giờ — 1 dòng/insight, không nút."""
    lines = [f"• {shorten(display_title(i))}" for i in insights]
    return DeliveryMessage(
        title=f"🔴 {len(insights)} tin đáng đọc ngay (gom do vượt trần tin/giờ)",
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
            lines.append(f"  {emoji} {shorten(display_title(i))}")
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
        """Quét insight trong lookback, alert cho subscriber có vai trò bị ảnh hưởng cao."""
        since = datetime.utcnow() - timedelta(hours=settings.delivery_alert_lookback_hours)
        insights = await self.insight_repo.list_for_delivery(since)
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
        candidates = [i for i in insights if alert_roles_match(sub.roles, i)]
        if not candidates:
            return 0, 0
        for i in candidates:
            logger.info(
                "[delivery] chat=%s nhận alert '%s' vì vai trò %s được chấm urgency=%s",
                sub.chat_id,
                (i.title or "")[:60],
                matched_alert_roles(sub.roles, i),
                ALERT_URGENCY_THRESHOLD,
            )
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
        """Gom phần còn lại trong lookback thành 1 digest/subscriber.

        "Phần còn lại" tính THEO TỪNG NGƯỜI: một tin alert cho Security vẫn là tin digest
        của người chỉ đăng ký Dev. Loại khỏi digest đúng những tin mà chính subscriber này
        đủ điều kiện nhận alert, tránh gửi hai lần cùng một tin.
        """
        since = datetime.utcnow() - timedelta(hours=settings.delivery_digest_lookback_hours)
        insights = await self.insight_repo.list_for_delivery(since)
        subscribers = await self.subscriber_repo.list_active()

        digests_sent = 0
        for sub in subscribers:
            candidates = [
                i
                for i in insights
                if roles_match(sub.roles, i.affected_roles)
                and not alert_roles_match(sub.roles, i)
            ]
            if not candidates:
                continue
            ids = [i.id for i in candidates]
            already = await self.log_repo.sent_insight_ids(sub.chat_id, "digest", ids)
            # Đã alert cho chính người này thì không nhắc lại trong digest. `alert_roles_match`
            # ở trên đã lo phần lớn; truy vấn này bắt nốt insight cũ từng alert theo luật
            # critical trước 2026-07-20 (không có role urgency nên lọt qua bộ lọc kia).
            already_alerted = await self.log_repo.sent_insight_ids(sub.chat_id, "alert", ids)
            todo = [
                i for i in candidates if i.id not in already and i.id not in already_alerted
            ]
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
