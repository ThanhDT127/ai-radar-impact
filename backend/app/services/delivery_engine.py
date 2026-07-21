"""Delivery Engine (M7) — bản tin định kỳ qua email, nhóm theo vai trò.

Chọn tin bằng XẾP HẠNG rồi lấy top-N cứng, không lọc theo ngưỡng: đo trên dữ liệu thật
(cửa sổ 108h) vai trò `Security` có 26 tin `urgency=high` còn `Data Scientist` có 0 —
lọc ngưỡng vừa làm ngập người này vừa bỏ đói người kia.

Vì mỗi kỳ chỉ gửi tối đa 3 tin nên mỗi tin render đầy đủ như trang chi tiết dashboard.
Format thuần template từ fields có sẵn — KHÔNG gọi Gemini ($0 AI).

Mọi text gửi đi phải là tiếng Việt, khớp dashboard — xem `display_title()`.
"""

import logging
import re
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.base import ChannelAdapter, DeliveryMessage
from app.channels.email_templates import render_brief
from app.config import settings
from app.models.insight import Insight
from app.models.subscriber import Subscriber
from app.repositories.delivery_log_repo import DeliveryLogRepository
from app.repositories.insight_repo import InsightRepository
from app.repositories.subscriber_repo import SubscriberRepository

logger = logging.getLogger(__name__)

DELIVERY_KIND = "brief"
COMPANY_WIDE_ROLE = "Toàn công ty"

# Thang điểm xếp hạng — thiếu khoá `urgency` hoặc giá trị ngoài tập đóng coi như medium,
# nhờ vậy insight cũ không bị đẩy lên đầu cũng không bị loại.
_ROLE_URGENCY_RANK = {"high": 3, "medium": 2, "low": 1}
_DEFAULT_URGENCY = "medium"
_IMPACT_RANK = {"Nghiêm trọng": 4, "Cao": 3, "Trung bình": 2, "Thấp": 1, "Theo dõi": 0}
_PRACTICAL_KEYS = ("has_security_patch", "has_api_change", "has_migration_guide")

# Dấu tiếng Việt — dùng để nhận biết title đã là tiếng Việt hay còn nguyên bản tiếng Anh.
# Giữ ĐỒNG BỘ với `hasVietnamese` trong `frontend/src/components/InsightCard.tsx`.
_VIETNAMESE_CHARS = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)


def has_vietnamese(text: str | None) -> bool:
    return bool(text) and bool(_VIETNAMESE_CHARS.search(text))


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
    """Subscriber nhận insight khi giao role khác rỗng; 'Toàn công ty' → mọi người."""
    if not subscriber_roles:
        return False
    affected = affected_roles or []
    if COMPANY_WIDE_ROLE in affected:
        return True
    return bool(set(subscriber_roles) & set(affected))


def role_urgency(insight: Insight, role: str) -> str:
    """`recommendations[role].urgency` — mức ảnh hưởng tới RIÊNG vai trò đó.

    KHÔNG phải cột vô hướng `insights.urgency` (cột đó suy tất định từ impact_label và
    trên dữ liệu thật không có giá trị `high` nào).
    """
    recs = insight.recommendations or {}
    if not isinstance(recs, dict):
        return _DEFAULT_URGENCY
    entry = recs.get(role)
    if not isinstance(entry, dict):
        return _DEFAULT_URGENCY
    value = entry.get("urgency")
    return value if value in _ROLE_URGENCY_RANK else _DEFAULT_URGENCY


def has_practical_indicator(insight: Insight) -> bool:
    """Có dấu hiệu cụ thể làm được ngay (bản vá, đổi API, hướng dẫn chuyển đổi)."""
    raw = insight.practical_indicators or {}
    return isinstance(raw, dict) and any(raw.get(k) for k in _PRACTICAL_KEYS)


def score_for_role(insight: Insight, role: str) -> tuple:
    """Điểm xếp hạng của một tin đối với MỘT vai trò — so sánh bằng tuple giảm dần."""
    when = insight.published_at or insight.created_at
    return (
        _ROLE_URGENCY_RANK[role_urgency(insight, role)],
        _IMPACT_RANK.get(insight.impact_label or "", 0),
        1 if has_practical_indicator(insight) else 0,
        insight.actionability_score or 0.0,
        1 if insight.intelligence_tier == "Strategic" else 0,
        insight.trust_score or 0.0,
        when.timestamp() if when else 0.0,
    )


def owning_role(subscriber_roles: list[str], insight: Insight) -> str:
    """Vai trò 'sở hữu' tin trong email — tin khớp nhiều vai trò chỉ hiện một lần.

    Ưu tiên vai trò giao với `affected_roles` và có điểm cao nhất; tin toàn công ty mà
    người nhận không đăng ký vai trò cụ thể nào thì xếp vào section "Toàn công ty".
    """
    affected = insight.affected_roles or []
    intersect = [r for r in subscriber_roles if r in affected]
    if not intersect:
        return COMPANY_WIDE_ROLE
    return max(intersect, key=lambda r: score_for_role(insight, r))


def select_for_subscriber(
    sub: Subscriber,
    insights: list[Insight],
    max_per_role: int | None = None,
    max_per_email: int | None = None,
) -> tuple[list[tuple[str, list[Insight]]], int]:
    """Chọn và sắp tin cho một người nhận.

    Trả `(sections, overflow)` — sections là `[(vai trò, [insight đã sắp])]` xếp từ khẩn
    cấp cao xuống thấp; overflow là số tin khớp nhưng không đủ chỗ.
    """
    per_role = max_per_role or settings.delivery_max_items_per_role
    per_email = max_per_email or settings.delivery_max_items_per_email

    candidates = [i for i in insights if roles_match(sub.roles, i.affected_roles)]
    if not candidates:
        return [], 0

    by_role: dict[str, list[tuple[tuple, Insight]]] = {}
    for insight in candidates:
        role = owning_role(sub.roles, insight)
        by_role.setdefault(role, []).append((score_for_role(insight, role), insight))

    # Trần mỗi vai trò trước, rồi trần toàn email trên phần còn lại
    ranked: list[tuple[tuple, str, Insight]] = []
    for role, scored in by_role.items():
        scored.sort(key=lambda pair: pair[0], reverse=True)
        ranked.extend((score, role, insight) for score, insight in scored[:per_role])

    ranked.sort(key=lambda triple: triple[0], reverse=True)
    selected = ranked[:per_email]
    overflow = len(candidates) - len(selected)

    # Gom lại thành section, giữ thứ tự: vai trò có tin khẩn cấp nhất lên trước
    sections: list[tuple[str, list[Insight]]] = []
    for _, role, insight in selected:
        for existing_role, items in sections:
            if existing_role == role:
                items.append(insight)
                break
        else:
            sections.append((role, [insight]))

    return sections, overflow


class DeliveryEngine:
    def __init__(self, session: AsyncSession, adapter: ChannelAdapter) -> None:
        self.insight_repo = InsightRepository(session)
        self.subscriber_repo = SubscriberRepository(session)
        self.log_repo = DeliveryLogRepository(session)
        self.adapter = adapter

    def _unsubscribe_url(self, sub: Subscriber) -> str:
        return f"{settings.public_api_base_url}/api/v1/unsubscribe?token={sub.unsubscribe_token}"

    def _build_message(
        self, sub: Subscriber, sections: list[tuple[str, list[Insight]]], overflow: int
    ) -> DeliveryMessage:
        titles = {i.id: display_title(i) for _, items in sections for i in items}
        unsubscribe_url = self._unsubscribe_url(sub)
        subject, text_body, html_body = render_brief(
            sections, titles, overflow, settings.dashboard_base_url, unsubscribe_url
        )
        return DeliveryMessage(
            title=subject,
            body=text_body,
            html_body=html_body,
            url=settings.dashboard_base_url,
            headers={
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        )

    async def build_for_subscriber(
        self, sub: Subscriber, insights: list[Insight]
    ) -> tuple[DeliveryMessage, list[Insight]] | None:
        """Dựng bản tin của một người, đã loại tin từng gửi. None nếu không có gì để gửi."""
        candidates = [i for i in insights if roles_match(sub.roles, i.affected_roles)]
        if not candidates:
            return None
        already = await self.log_repo.sent_insight_ids(
            sub.id, DELIVERY_KIND, [i.id for i in candidates]
        )
        fresh = [i for i in candidates if i.id not in already]
        if not fresh:
            return None

        sections, overflow = select_for_subscriber(sub, fresh)
        if not sections:
            return None
        chosen = [i for _, items in sections for i in items]
        return self._build_message(sub, sections, overflow), chosen

    async def run_brief(self, dry_run: bool = False, force: bool = False) -> dict[str, int]:
        """Một kỳ bản tin: mỗi người nhận tối đa 1 email, tin sắp theo mức khẩn cấp.

        `dry_run` dựng nội dung nhưng không gửi và không ghi log.
        `force` bỏ qua chốt chặn chu kỳ — chỉ dùng khi test.
        """
        since = datetime.utcnow() - timedelta(hours=settings.delivery_digest_lookback_hours)
        insights = await self.insight_repo.list_for_delivery(since)
        subscribers = await self.subscriber_repo.list_active()

        sent = failed = skipped = 0
        if not dry_run:
            # dry-run không được mở kết nối SMTP thật — chỉ dựng nội dung
            await self.adapter.open()
        try:
            for sub in subscribers:
                # Chốt chặn chu kỳ: unique constraint chỉ chặn GỬI LẠI CÙNG MỘT TIN.
                # Lần chạy thừa trong cùng kỳ sẽ lấy 3 tin xếp hạng kế tiếp — vẫn là tin
                # khác nên lọt qua constraint. Guard này mới là thứ chặn nó.
                if not force and await self.log_repo.sent_within(
                    sub.id, DELIVERY_KIND, settings.delivery_min_gap_hours
                ):
                    skipped += 1
                    continue

                built = await self.build_for_subscriber(sub, insights)
                if built is None:
                    skipped += 1  # không gửi email rỗng
                    continue
                message, chosen = built

                if dry_run:
                    print(f"\n{'=' * 70}\nTO: {sub.email}\nSUBJECT: {message.title}\n{'=' * 70}")
                    print(message.body)
                    sent += 1
                    continue

                result = await self.adapter.send(sub.email, message)
                if result.ok:
                    # Chỉ log tin THỰC SỰ gửi — tin bị loại vì trần còn cạnh tranh kỳ sau
                    await self.log_repo.log_sent([i.id for i in chosen], sub.id, DELIVERY_KIND)
                    sent += 1
                else:
                    failed += 1
        finally:
            if not dry_run:
                await self.adapter.close()

        logger.info(
            "[delivery] Bản tin: sent=%d failed=%d skipped=%d (dry_run=%s)",
            sent, failed, skipped, dry_run,
        )
        return {"sent": sent, "failed": failed, "skipped": skipped}
