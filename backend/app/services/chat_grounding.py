"""Grounding cho chat: đánh số candidate, dựng index, giải marker [n] thành citation.

Cốt lõi của design D4 — **server cấp phát định danh, model chỉ đánh dấu**:

    server  ──▶  [1] Anthropic ra MCP…      (prompt KHÔNG chứa UUID)
                 [2] EU AI Act giai đoạn 2…
    model   ──▶  "…MCP đang thành chuẩn [1]."   (text thuần)
    server  ──▶  tra bảng n → insight_id  ──▶  citations đầy đủ

Model không bao giờ nhìn thấy UUID nên không có gì để bịa. Đây là lý do chống bịa
citation ở đây là *cấu trúc*, không phải hậu kiểm lọc id lạ.
"""

import re
import uuid

from app.ai.prompts import OUT_OF_SCOPE_SENTINEL
from app.models.insight import Insight

# Marker dạng [1], [12] — không khớp [abc] hay [1.5].
_MARKER_RE = re.compile(r"\[(\d+)\]")

# Câu trả lời "không tìm thấy" hợp lệ thì không cần citation (design D4). Nhận diện
# bằng cụm từ vì prompt đã yêu cầu model dùng đúng câu này.
_NOT_FOUND_MARKERS = (
    "không tìm thấy",
    "không có thông tin",
    "chưa có tin nào",
    "không đủ dữ liệu",
)

INSUFFICIENT_GROUNDS_MESSAGE = (
    "Tôi không đủ căn cứ trong hệ thống để trả lời câu hỏi này. "
    "Bạn thử hỏi cụ thể hơn, hoặc xem trực tiếp trên dashboard nhé."
)


def _fmt_date(insight: Insight) -> str:
    when = insight.published_at or insight.created_at
    return when.strftime("%d/%m/%Y") if when else "không rõ ngày"


def build_index_block(
    insights: list[Insight], start: int = 1
) -> tuple[str, dict[int, Insight]]:
    """Dựng index nén đã đánh số + bảng ánh xạ `n → Insight`.

    Một dòng ≈ 108 token (đo trên corpus 22/07/2026: title 60 + signal 144 ký tự).
    KHÔNG đưa UUID vào chuỗi trả về — đó là toàn bộ điểm của D4.

    `start` cho phép chế độ mở rộng (`chat-scope-routing`) dành [1] cho bài đang xem rồi
    đánh số tin toàn cục từ [2]. Một dãy số liên tục qua cả hai khối context ⇒ vẫn đúng
    MỘT bảng ánh xạ, không phải hai không gian số chồng nhau.
    """
    lines: list[str] = []
    mapping: dict[int, Insight] = {}

    for n, insight in enumerate(insights, start=start):
        mapping[n] = insight
        roles = ", ".join(insight.affected_roles or []) or "—"
        topics = ", ".join(insight.topics or []) or "—"
        signal = (insight.signal or insight.summary_short or "").strip()
        lines.append(
            f"[{n}] {insight.title}\n"
            f"    Ý nghĩa: {signal}\n"
            f"    Vai trò: {roles} | Chủ đề: {topics} | Ngày: {_fmt_date(insight)}"
        )

    return "\n".join(lines), mapping


def build_insight_block(insight: Insight, content: str | None) -> str:
    """Context chế độ per-insight — luôn đánh số [1] vì chỉ có đúng 1 nguồn."""
    parts = [f"[1] {insight.title}"]

    def add(label: str, value) -> None:
        if value:
            parts.append(f"    {label}: {value}")

    add("Ý nghĩa", insight.signal)
    add("Vì sao quan trọng", insight.why_it_matters)
    add("So what", insight.so_what)
    add("Tóm tắt", insight.summary_medium)
    add("Vai trò ảnh hưởng", ", ".join(insight.affected_roles or []))
    add("Chủ đề", ", ".join(insight.topics or []))
    add("Rủi ro", "; ".join(insight.risks or []))

    if insight.recommendations:
        recs = []
        for role, entry in insight.recommendations.items():
            if isinstance(entry, dict):
                note = entry.get("note", "")
                action = entry.get("action_type", "")
                recs.append(f"{role} ({action}): {note}")
        add("Khuyến nghị", " | ".join(recs))

    add("Ngày", _fmt_date(insight))

    if content:
        parts.append(f"\n    NỘI DUNG BÀI GỐC:\n{content}")
    else:
        # Tombstone-purge xoá normalized_content sau retention_months nhưng giữ insight.
        parts.append(
            "\n    (Bài gốc đã hết hạn lưu trữ — chỉ còn phần phân tích ở trên. "
            "Nếu câu hỏi cần chi tiết trong bài gốc, hãy nói rõ là không còn dữ liệu.)"
        )

    return "\n".join(parts)


def resolve_citations(
    answer: str, mapping: dict[int, Insight]
) -> tuple[str, list[dict]]:
    """Giải marker [n] → citations; bỏ marker ngoài phạm vi, GIỮ nội dung answer.

    Trả `(answer_đã_dọn, citations)`. Citations giữ thứ tự xuất hiện, không trùng lặp.
    """
    seen: list[int] = []
    for raw in _MARKER_RE.findall(answer):
        n = int(raw)
        if n in mapping and n not in seen:
            seen.append(n)

    cleaned = _MARKER_RE.sub(
        lambda m: m.group(0) if int(m.group(1)) in mapping else "", answer
    )
    # Bỏ marker có thể để lại khoảng trắng thừa trước dấu câu.
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()

    citations = [
        {
            "insight_id": mapping[n].id,
            "title": mapping[n].title,
            "source_url": mapping[n].source_url,
        }
        for n in seen
    ]
    return cleaned, citations


def is_out_of_scope_answer(raw_answer: str) -> bool:
    """Lượt gọi chế độ B có phát sentinel ngoài‑phạm‑vi không? (design D3)

    Đọc trên văn bản **thô**, TRƯỚC `resolve_citations`/`enforce_grounding` — sentinel
    không có marker `[n]` nào nên nếu để grounding chạy trước thì nó bị thay bằng
    `INSUFFICIENT_GROUNDS_MESSAGE` và tín hiệu biến mất.

    Nhận diện CHẶT theo đúng bias dè dặt: chỉ khi sentinel là **toàn bộ** câu trả lời.
    Model vừa trả lời vừa kèm sentinel nghĩa là nó trả lời được → không mở rộng, vì mở
    nhầm tốn gấp đôi lượt gọi và độ trễ. Chỉ nới đúng phần rác định dạng model hay thêm
    (dấu nháy ngược, khoảng trắng).
    """
    stripped = raw_answer.strip().strip("`").strip()
    return stripped == OUT_OF_SCOPE_SENTINEL


def is_not_found_answer(answer: str) -> bool:
    """Câu trả lời thuộc dạng 'không tìm thấy' — được phép không có citation."""
    lowered = answer.lower()
    return any(marker in lowered for marker in _NOT_FOUND_MARKERS)


def enforce_grounding(answer: str, citations: list[dict]) -> tuple[str, list[dict]]:
    """Fail-closed: khẳng định mà không có marker nào → thay bằng thông báo.

    Ngược chiều với gate analysis (fail-open): ở đó mất bài còn cứu được ở lần crawl
    sau, còn chat trả lời sai thì người dùng mang đi quyết định.
    """
    if citations:
        return answer, citations
    if is_not_found_answer(answer):
        return answer, []
    return INSUFFICIENT_GROUNDS_MESSAGE, []
