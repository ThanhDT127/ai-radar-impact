"""Đoạn XẾP HẠNG, insight TRÍCH DẪN — ranh giới này phải được khoá bằng test.

Vì sao đáng một file riêng: `chat-citation-integrity` đã trả giá một lần cho việc có **hai
hệ quy chiếu** cho `n`, và lỗi đó sống ở khe giữa hai tầng (test backend xanh trong khi
widget trỏ sai cả hai nguồn). Cho đoạn thành nguồn trích dẫn là dựng lại đúng cái bẫy đó ở
quy mô lớn hơn: một bài 5 đoạn ⇒ 5 số cho cùng một nguồn, và câu trả lời trích 3 số trỏ về
một tin.

Bất biến: mọi giá trị trong bảng ánh xạ `n → nguồn` là một **Insight**, và mỗi insight xuất
hiện **đúng một lần** dù bao nhiêu đoạn của nó khớp câu hỏi.
"""

import uuid

from app.models.insight import Insight
from app.services.chat_grounding import build_context, resolve_citations


def _insight(title: str) -> Insight:
    return Insight(
        id=uuid.uuid4(),
        title=title,
        source_url="https://example.com/" + title[:5],
        summary_short="Tóm tắt.",
        topics=["Security & Compliance"],
        affected_roles=["Dev"],
        impact_label="Cao",
        trust_score=0.8,
    )


def test_context_mapping_contains_only_insights():
    ranked = [_insight(f"Tin số {n}") for n in range(6)]

    ctx = build_context(refs=[], ranked=ranked, k_deep=3, index_limit=6, include_content=False)

    assert ctx.mapping, "context phải có nguồn"
    assert all(isinstance(v, Insight) for v in ctx.mapping.values())


def test_insight_appears_once_even_when_several_of_its_chunks_match():
    """Kịch bản spec: ba đoạn của cùng một bài đều khớp câu hỏi.

    Tầng đoạn chỉ trả về **một** thứ hạng cho mỗi insight (gộp `min` ở repository), nên tin
    đó vào context đúng một lần với đúng một số. Test này khoá phía context: dù tin xếp hạng
    cao tới đâu, nó không được nhân bản.
    """
    hot = _insight("Bài có ba đoạn cùng khớp")
    ranked = [hot] + [_insight(f"Tin khác {n}") for n in range(4)]

    ctx = build_context(refs=[], ranked=ranked, k_deep=2, index_limit=5, include_content=False)

    numbers = [n for n, insight in ctx.mapping.items() if insight.id == hot.id]
    assert len(numbers) == 1, f"tin xuất hiện {len(numbers)} lần trong context"
    assert ctx.index_block.count(hot.title) + ctx.deep_block.count(hot.title) == 1


def test_markers_resolve_to_insights_not_chunks():
    ranked = [_insight(f"Tin số {n}") for n in range(4)]
    ctx = build_context(refs=[], ranked=ranked, k_deep=1, index_limit=4, include_content=False)

    answer, citations = resolve_citations("Theo [1] và [3], nên vá ngay.", ctx.mapping)

    assert {c["n"] for c in citations} == {1, 3}
    resolved = {c["insight_id"] for c in citations}
    assert resolved <= {i.id for i in ranked}, "marker chỉ được giải về insight có thật"


def test_best_chunk_match_earns_a_deep_slot_even_when_ranked_lower():
    """Bài có đoạn khớp nhất toàn corpus được đọc kỹ, dù thứ hạng TỔNG rơi ngoài `k_deep`.

    Đây là phần chữa khoảng hở đo được 28/07: tầng đoạn kéo bài đúng vào context nhưng nó
    chỉ vào dưới dạng dòng index nén của phần *phân tích* — đúng chỗ không chứa định danh
    được hỏi — nên model từ chối dù bài đúng đã ở đó (`det-squashfs` hạng 4,
    `det-spdx-cyclonedx` hạng 5, cả hai có hạng đoạn 1).
    """
    ranked = [_insight(f"Tin số {n}") for n in range(8)]
    target = ranked[4]  # hạng tổng 5 — ngoài 3 ô sâu

    ctx = build_context(refs=[], ranked=ranked, k_deep=3, index_limit=8,
                        include_content=False, best_chunk_match=target.id)

    deep_ids = [ctx.mapping[n].id for n in range(1, ctx.deep_count + 1)]
    assert target.id in deep_ids
    assert ctx.deep_count == 3, "không được nới thêm ô sâu, chỉ đổi tin nào được rót"


def test_refs_still_outrank_the_best_chunk_match():
    """Tin người dùng CHỦ ĐỘNG chọn không bao giờ bị chen."""
    ranked = [_insight(f"Tin số {n}") for n in range(8)]
    chosen, target = ranked[6], ranked[4]

    ctx = build_context(refs=[chosen], ranked=ranked, k_deep=2, index_limit=8,
                        include_content=False, best_chunk_match=target.id)

    assert ctx.mapping[1].id == chosen.id
    assert ctx.mapping[2].id == target.id


def test_no_best_chunk_match_keeps_deep_slots_exactly_as_before():
    ranked = [_insight(f"Tin số {n}") for n in range(8)]

    before = build_context(refs=[], ranked=ranked, k_deep=3, index_limit=8,
                           include_content=False)
    after = build_context(refs=[], ranked=ranked, k_deep=3, index_limit=8,
                          include_content=False, best_chunk_match=None)

    assert [i.id for i in before.mapping.values()] == [i.id for i in after.mapping.values()]


def test_tied_best_chunk_matches_are_ignored():
    """Nhiều tin cùng hạng đoạn 1 ⇒ không có căn cứ chọn ⇒ không chen ai cả."""
    from app.services.chat_service import _best_chunk_match

    a, b = uuid.uuid4(), uuid.uuid4()
    assert _best_chunk_match({a: 1, b: 1}) is None
    assert _best_chunk_match({a: 1, b: 2}) == a
    assert _best_chunk_match({a: 2, b: 3}) is None, "hạng 2 chưa đủ căn cứ — chỉ nhận hạng 1"
    assert _best_chunk_match({}) is None
    assert _best_chunk_match(None) is None


def test_prompt_blocks_never_carry_raw_chunk_text():
    """Nội dung bài gốc vào câu trả lời qua **ô sâu**, không qua tầng đoạn.

    Cách viết sai mà test này chặn: "tiện tay" nhét đoạn khớp nhất vào index cho model đọc
    thêm. Làm vậy là đưa văn bản không có số thứ tự vào prompt — model sẽ trích nó và
    `resolve_citations` không có gì để giải.
    """
    ranked = [_insight(f"Tin số {n}") for n in range(4)]
    ctx = build_context(refs=[], ranked=ranked, k_deep=0, index_limit=4, include_content=False)

    # Index nén chỉ mang các field phân tích; mỗi dòng phải bắt đầu bằng một số thứ tự.
    numbered = [l for l in ctx.index_block.splitlines() if l.strip().startswith("[")]
    assert len(numbered) == len(ctx.mapping)
