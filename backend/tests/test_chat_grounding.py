"""Grounding chat: server cấp phát citation, model chỉ đánh dấu (design D4).

Điểm cần khoá lại: prompt KHÔNG được chứa UUID. Nếu một ngày ai đó thêm id vào index
"cho tiện", model sẽ có thứ để bịa và toàn bộ luận điểm chống-bịa-bằng-cấu-trúc sụp.
"""

import uuid
from datetime import datetime

from app.services.chat_grounding import (
    INSUFFICIENT_GROUNDS_MESSAGE,
    build_index_block,
    build_insight_block,
    enforce_grounding,
    is_not_found_answer,
    resolve_citations,
)


class _FakeInsight:
    def __init__(self, title="Tin thử", signal="Ý nghĩa thử", **kw):
        self.id = kw.get("id", uuid.uuid4())
        self.title = title
        self.signal = signal
        self.summary_short = kw.get("summary_short", "tóm tắt ngắn")
        self.summary_medium = kw.get("summary_medium", "tóm tắt vừa")
        self.why_it_matters = kw.get("why_it_matters", "vì sao quan trọng")
        self.so_what = kw.get("so_what", "so what")
        self.risks = kw.get("risks", ["rủi ro A"])
        self.recommendations = kw.get(
            "recommendations", {"Dev": {"action_type": "read", "note": "đọc đi"}}
        )
        self.affected_roles = kw.get("affected_roles", ["Dev", "Tech Lead"])
        self.topics = kw.get("topics", ["AI/ML Ứng dụng"])
        self.source_url = kw.get("source_url", "https://example.com/a")
        self.published_at = kw.get("published_at", datetime(2026, 7, 20, 10, 0))
        self.created_at = datetime(2026, 7, 21, 10, 0)


def test_index_block_never_leaks_uuid():
    """Bất biến quan trọng nhất của D4."""
    insights = [_FakeInsight(title=f"Tin {i}") for i in range(3)]
    block, mapping = build_index_block(insights)

    for insight in insights:
        assert str(insight.id) not in block, "UUID bị rò vào prompt — model sẽ bịa được id"
    assert set(mapping) == {1, 2, 3}
    assert "[1]" in block and "[3]" in block


def test_insight_block_never_leaks_uuid():
    insight = _FakeInsight()
    block = build_insight_block(insight, "nội dung bài gốc")
    assert str(insight.id) not in block
    assert block.startswith("[1] ")


def test_insight_block_notes_expired_original():
    """Tombstone-purge xoá normalized_content nhưng giữ insight."""
    block = build_insight_block(_FakeInsight(), None)
    assert "hết hạn lưu trữ" in block
    assert "NỘI DUNG BÀI GỐC" not in block


def test_resolve_citations_maps_markers_in_order():
    a, b = _FakeInsight(title="A"), _FakeInsight(title="B")
    mapping = {1: a, 2: b}

    answer, citations = resolve_citations("Chuyện B [2] rồi chuyện A [1].", mapping)

    assert [c["title"] for c in citations] == ["B", "A"], "citation giữ thứ tự xuất hiện"
    assert citations[0]["insight_id"] == b.id
    assert "[2]" in answer and "[1]" in answer


def test_resolve_citations_deduplicates():
    a = _FakeInsight(title="A")
    _, citations = resolve_citations("Câu một [1]. Câu hai cũng [1].", {1: a})
    assert len(citations) == 1


def test_out_of_range_marker_dropped_but_answer_kept():
    """Marker lạ chỉ bị gỡ khỏi text — KHÔNG được vứt cả câu trả lời."""
    a = _FakeInsight(title="A")
    answer, citations = resolve_citations(
        "Điều này đúng [1] và điều kia [99] cũng vậy.", {1: a}
    )

    assert "[99]" not in answer
    assert "điều kia" in answer, "nội dung answer phải được giữ nguyên"
    assert len(citations) == 1


def test_marker_removal_does_not_leave_space_before_punctuation():
    a = _FakeInsight()
    answer, _ = resolve_citations("Một khẳng định [42].", {1: a})
    assert answer == "Một khẳng định."


def test_enforce_grounding_blocks_unsourced_assertion():
    answer, citations = enforce_grounding("Gemini 3 ra mắt hôm qua.", [])
    assert answer == INSUFFICIENT_GROUNDS_MESSAGE
    assert citations == []


def test_enforce_grounding_lets_not_found_through():
    original = "Không tìm thấy thông tin này trong hệ thống."
    answer, citations = enforce_grounding(original, [])
    assert answer == original
    assert citations == []


def test_enforce_grounding_passes_cited_answer():
    cites = [{"insight_id": uuid.uuid4(), "title": "A", "source_url": "u"}]
    answer, citations = enforce_grounding("Có chuyện này [1].", cites)
    assert answer == "Có chuyện này [1]."
    assert citations == cites


def test_is_not_found_detects_role_without_data():
    assert is_not_found_answer("Chưa có tin nào cho vai trò Data Analyst.")


def test_empty_index_block():
    block, mapping = build_index_block([])
    assert block == ""
    assert mapping == {}
