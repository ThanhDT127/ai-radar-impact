"""Render bản tin email — thuần f-string, KHÔNG gọi AI, không thêm template engine.

Trả về `(subject, text_body, html_body)`. HTML dùng CSS inline + layout `<table>` vì
Gmail/Outlook không hỗ trợ `<style>` ngoài, flexbox hay grid.

Nhãn hiển thị giữ ĐỒNG BỘ với dashboard (`InsightDetail.tsx`, `RecommendationsByRole.tsx`)
— cùng một tin phải đọc giống nhau ở hai nơi.
"""

from datetime import datetime
from html import escape

from app.models.insight import Insight

# Gmail cắt subject quanh ~70 ký tự trên desktop và ngắn hơn nữa trên mobile.
SUBJECT_MAX = 100

TIER_LABEL = {
    "Tactical": "Hành động ngay",
    "Operational": "Vận hành",
    "Strategic": "Chiến lược",
    "Informational": "Tham khảo",
}

ADOPTION_LABEL = {
    "Adopt": "Áp dụng",
    "Trial": "Dùng thử",
    "Assess": "Đánh giá",
    "Hold": "Tạm hoãn",
}

ACTION_LABEL = {
    "watch": "Theo dõi",
    "read": "Đọc kỹ",
    "test": "Thử nghiệm",
    "PoC": "Đề xuất PoC",
    "roadmap": "Vào roadmap",
}

INDICATOR_LABEL = {
    "has_code_example": "💻 Mã nguồn",
    "has_benchmark": "📊 Benchmark",
    "has_api_change": "🔗 API",
    "has_migration_guide": "📖 Hướng dẫn chuyển đổi",
    "has_security_patch": "🛡️ Bản vá bảo mật",
}

URGENCY_LABEL = {"high": "Ảnh hưởng cao", "medium": "Ảnh hưởng vừa", "low": "Ảnh hưởng thấp"}


def shorten_subject(text: str, limit: int = SUBJECT_MAX) -> str:
    """Cắt subject ở ranh giới từ — thân email KHÔNG cắt tiêu đề."""
    if len(text) <= limit:
        return text
    return f"{text[:limit].rsplit(' ', 1)[0].rstrip(' ,.;:–-')}…"


def indicators_of(insight: Insight) -> list[str]:
    raw = insight.practical_indicators or {}
    if not isinstance(raw, dict):
        return []
    return [label for key, label in INDICATOR_LABEL.items() if raw.get(key)]


def badges_of(insight: Insight) -> list[str]:
    badges = []
    if insight.impact_label:
        badges.append(insight.impact_label)
    if insight.intelligence_tier:
        badges.append(TIER_LABEL.get(insight.intelligence_tier, insight.intelligence_tier))
    if insight.adoption_ring:
        badges.append(ADOPTION_LABEL.get(insight.adoption_ring, insight.adoption_ring))
    return badges


def recommendation_for(insight: Insight, role: str) -> tuple[str, str] | None:
    """`(nhãn hành động, ghi chú)` của đúng vai trò chứa tin này."""
    recs = insight.recommendations or {}
    entry = recs.get(role) if isinstance(recs, dict) else None
    if not isinstance(entry, dict):
        return None
    action = ACTION_LABEL.get(entry.get("action_type", ""), entry.get("action_type") or "")
    note = (entry.get("note") or "").strip()
    if not action and not note:
        return None
    return action, note


def build_subject(sections: list[tuple[str, list[Insight]]], overflow: int, titles: dict) -> str:
    """Subject = tiêu đề tin xếp hạng cao nhất + số tin CÒN LẠI TRONG EMAIL.

    Người đọc quyết định mở hay không ngay từ inbox, thay vì một tiêu đề chung chung.
    Đuôi đếm KHÔNG cộng `overflow`: "+146 tin khác" chỉ gây hoảng, còn số tin thực sự
    phải đọc là 3. Overflow chỉ xuất hiện ở chân email kèm link dashboard.
    """
    top_title = titles[sections[0][1][0].id]
    total = sum(len(items) for _, items in sections)
    tail = f" +{total - 1} tin khác" if total > 1 else ""
    prefix = f"AI Radar {datetime.now():%d/%m}: "
    return prefix + shorten_subject(top_title, SUBJECT_MAX - len(prefix) - len(tail)) + tail


# ── Plain text ───────────────────────────────────────────────────────────────


def _text_item(index: int, insight: Insight, role: str, title: str, dashboard_url: str) -> str:
    lines = [f"{index}. {title}"]

    meta = badges_of(insight) + indicators_of(insight)
    if meta:
        lines.append(f"   [{'] ['.join(meta)}]")
    lines.append("")

    for label, value in (
        ("Tín hiệu", insight.signal),
        ("Điều đáng nói", insight.so_what),
        ("Vì sao quan trọng", insight.why_it_matters),
        ("Tóm tắt", insight.summary_medium),
    ):
        if value:
            lines.append(f"   {label}: {value.strip()}")
            lines.append("")

    rec = recommendation_for(insight, role)
    if rec:
        action, note = rec
        lines.append(f"   Khuyến nghị cho {role} — {action}: {note}")
        lines.append("")

    if insight.risks:
        lines.append("   Rủi ro:")
        lines.extend(f"     - {r}" for r in insight.risks)
        lines.append("")

    lines.append(f"   Đọc chi tiết: {dashboard_url}/insights/{insight.id}")
    return "\n".join(lines)


def render_text(
    sections: list[tuple[str, list[Insight]]],
    titles: dict,
    overflow: int,
    dashboard_url: str,
    unsubscribe_url: str,
) -> str:
    total = sum(len(items) for _, items in sections)
    roles = ", ".join(role for role, _ in sections)
    out = [
        f"BẢN TIN AI RADAR — {datetime.now():%d/%m/%Y}",
        f"{total} tin cho vai trò: {roles}",
        "=" * 60,
        "",
    ]

    index = 0
    for role, items in sections:
        out.append(f"▼ {role.upper()}")
        out.append("")
        for insight in items:
            index += 1
            out.append(_text_item(index, insight, role, titles[insight.id], dashboard_url))
            out.append("")

    out.append("-" * 60)
    if overflow > 0:
        out.append(f"+{overflow} tin khác — xem trên dashboard: {dashboard_url}")
    out.append("Bạn nhận email này vì đã đăng ký nhận bản tin AI Radar theo vai trò.")
    out.append(f"Hủy nhận: {unsubscribe_url}")
    return "\n".join(out)


# ── HTML ─────────────────────────────────────────────────────────────────────

_WRAP = "font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
_MUTED = "color:#6b7280;font-size:13px;"
_BADGE = (
    "display:inline-block;padding:2px 8px;margin:0 4px 4px 0;border-radius:10px;"
    "background:#f1f5f9;color:#334155;font-size:12px;"
)


def _html_item(index: int, insight: Insight, role: str, title: str, dashboard_url: str) -> str:
    parts = [
        f'<tr><td style="padding:20px 0 0 0;border-top:1px solid #e5e7eb;">',
        f'<div style="font-size:17px;font-weight:600;color:#111827;line-height:1.4;">'
        f"{index}. {escape(title)}</div>",
    ]

    meta = badges_of(insight) + indicators_of(insight)
    if meta:
        badges = "".join(f'<span style="{_BADGE}">{escape(m)}</span>' for m in meta)
        parts.append(f'<div style="margin:8px 0;">{badges}</div>')

    for label, value in (
        ("Tín hiệu", insight.signal),
        ("Điều đáng nói", insight.so_what),
        ("Vì sao quan trọng", insight.why_it_matters),
        ("Tóm tắt", insight.summary_medium),
    ):
        if value:
            parts.append(
                f'<p style="margin:8px 0;font-size:14px;line-height:1.6;color:#374151;">'
                f'<strong style="color:#111827;">{label}:</strong> {escape(value.strip())}</p>'
            )

    rec = recommendation_for(insight, role)
    if rec:
        action, note = rec
        parts.append(
            f'<div style="margin:12px 0;padding:10px 12px;background:#f8fafc;'
            f'border-left:3px solid #2563eb;font-size:14px;line-height:1.6;">'
            f'<strong>Khuyến nghị cho {escape(role)} — {escape(action)}:</strong> '
            f"{escape(note)}</div>"
        )

    if insight.risks:
        items = "".join(f"<li>{escape(r)}</li>" for r in insight.risks)
        parts.append(
            f'<div style="margin:8px 0;font-size:14px;color:#374151;"><strong>Rủi ro:</strong>'
            f'<ul style="margin:4px 0 0 18px;padding:0;line-height:1.6;">{items}</ul></div>'
        )

    parts.append(
        f'<p style="margin:12px 0 20px 0;"><a href="{dashboard_url}/insights/{insight.id}" '
        f'style="color:#2563eb;text-decoration:none;font-size:14px;">Đọc chi tiết →</a></p>'
    )
    parts.append("</td></tr>")
    return "".join(parts)


def render_html(
    sections: list[tuple[str, list[Insight]]],
    titles: dict,
    overflow: int,
    dashboard_url: str,
    unsubscribe_url: str,
) -> str:
    total = sum(len(items) for _, items in sections)
    roles = ", ".join(role for role, _ in sections)

    rows = [
        f'<tr><td style="padding-bottom:16px;">'
        f'<div style="font-size:20px;font-weight:700;color:#111827;">Bản tin AI Radar</div>'
        f'<div style="{_MUTED}">{datetime.now():%d/%m/%Y} · {total} tin cho vai trò: '
        f"{escape(roles)}</div></td></tr>"
    ]

    index = 0
    for role, items in sections:
        rows.append(
            f'<tr><td style="padding:18px 0 4px 0;font-size:13px;font-weight:700;'
            f'letter-spacing:.5px;color:#2563eb;text-transform:uppercase;">{escape(role)}</td></tr>'
        )
        for insight in items:
            index += 1
            rows.append(_html_item(index, insight, role, titles[insight.id], dashboard_url))

    footer = []
    if overflow > 0:
        footer.append(
            f'<a href="{dashboard_url}" style="color:#2563eb;text-decoration:none;">'
            f"+{overflow} tin khác — xem trên dashboard</a><br>"
        )
    footer.append(
        "Bạn nhận email này vì đã đăng ký nhận bản tin AI Radar theo vai trò.<br>"
        f'<a href="{unsubscribe_url}" style="color:#6b7280;">Hủy nhận</a>'
    )
    rows.append(
        f'<tr><td style="padding-top:20px;border-top:1px solid #e5e7eb;{_MUTED}">'
        f'{"".join(footer)}</td></tr>'
    )

    return (
        f'<div style="{_WRAP}background:#ffffff;padding:24px;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'style="max-width:640px;width:100%;">{"".join(rows)}</table></div>'
    )


def render_brief(
    sections: list[tuple[str, list[Insight]]],
    titles: dict,
    overflow: int,
    dashboard_url: str,
    unsubscribe_url: str,
) -> tuple[str, str, str]:
    """`(subject, text_body, html_body)` cho một bản tin đã chọn xong tin."""
    return (
        build_subject(sections, overflow, titles),
        render_text(sections, titles, overflow, dashboard_url, unsubscribe_url),
        render_html(sections, titles, overflow, dashboard_url, unsubscribe_url),
    )
