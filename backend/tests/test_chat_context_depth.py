"""Ô SÂU + working set (`chat-context-depth`).

Bất biến cần khoá:
- `build_context` là **hàm thuần**, lấp ô sâu TẤT ĐỊNH (refs trước, xếp hạng sau);
- một tin KHÔNG BAO GIỜ mang hai số (ô sâu phải biến mất khỏi index);
- `index_limit` đếm CẢ ô sâu — trần top-K không được thành lời nói suông;
- ref chết bị bỏ **lặng lẽ**, không 404;
- marker `[n]` trong history giải thành TÊN BÀI, vì bảng ánh xạ dựng lại mỗi lượt.
"""

import uuid
from datetime import datetime

import pytest

from app.services.chat_grounding import build_context
from app.services.chat_service import ChatService, _history_block


class _FakeInsight:
    def __init__(self, title, content=None, role_urgency="medium"):
        self.id = uuid.uuid4()
        self.title = title
        self.signal = f"Ý nghĩa của {title}"
        self.why_it_matters = f"Vì sao {title} quan trọng"
        self.so_what = f"Nên làm gì với {title}"
        self.summary_short = "ngắn"
        self.summary_medium = "vừa"
        self.risks = []
        self.affected_roles = ["Security"]
        self.topics = ["Security & Compliance"]
        self.source_url = f"https://example.com/{title}"
        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.impact_label = "Trung bình"
        self.actionability_score = 0.5
        self.intelligence_tier = "Tactical"
        self.trust_score = 0.8
        self.practical_indicators = None
        self.recommendations = {
            "Security": {"action_type": "read", "note": "n", "urgency": role_urgency}
        }
        self.raw_document = _FakeRawDoc(content) if content is not None else None


class _FakeRawDoc:
    def __init__(self, content):
        self.normalized_content = content


class _Turn:
    def __init__(self, role, content, citations=()):
        self.role = role
        self.content = content
        self.citations = list(citations)


class _Cit:
    def __init__(self, n, title):
        self.n = n
        self.title = title


# --- build_context: hàm thuần -----------------------------------------------------------


def test_refs_fill_deep_slots_first_then_ranking():
    a, b, c, d = (_FakeInsight(t) for t in "ABCD")
    ctx = build_context(refs=[c, d], ranked=[a, b, c, d], k_deep=3, index_limit=60)

    assert ctx.deep_count == 3
    # [1][2] là refs theo ĐÚNG thứ tự client gửi; [3] lấp bằng tin xếp hạng cao nhất còn lại.
    assert ctx.mapping[1] is c
    assert ctx.mapping[2] is d
    assert ctx.mapping[3] is a
    assert ctx.mapping[4] is b


def test_deep_slot_insight_disappears_from_index():
    a, b = _FakeInsight("A"), _FakeInsight("B")
    ctx = build_context(refs=[b], ranked=[a, b], k_deep=1, index_limit=60)

    numbers = [n for n, i in ctx.mapping.items() if i is b]
    assert numbers == [1], "tin ở ô sâu không được xuất hiện lại trong index"
    assert f"[2] {b.title}" not in ctx.index_block


def test_no_refs_hydrates_top_ranked():
    """②′ — câu toàn cục không ghim gì vẫn được ô sâu, không cần ai bấm."""
    items = [_FakeInsight(t) for t in "ABCDE"]
    ctx = build_context(refs=[], ranked=items, k_deep=3, index_limit=60)

    assert ctx.deep_count == 3
    assert [ctx.mapping[n] for n in (1, 2, 3)] == items[:3]


def test_index_limit_counts_deep_slots():
    """Trần top-K đếm CẢ ô sâu — `k_deep=3` + `index_limit=1` phải cho đúng 1 tin.

    Bỏ luật này thì trần trở thành lời nói suông đúng ở cấu hình chặt nhất.
    """
    items = [_FakeInsight(t) for t in "ABCDE"]
    ctx = build_context(refs=[], ranked=items, k_deep=3, index_limit=1)

    assert ctx.deep_count == 1
    assert len(ctx.mapping) == 1
    assert ctx.hidden == 4


def test_duplicate_refs_do_not_consume_two_slots():
    a, b = _FakeInsight("A"), _FakeInsight("B")
    ctx = build_context(refs=[a, a], ranked=[a, b], k_deep=2, index_limit=60)

    assert ctx.deep_count == 2
    assert [ctx.mapping[1], ctx.mapping[2]] == [a, b]


def test_deep_block_carries_content_and_can_be_switched_off():
    a = _FakeInsight("A", content="THÂN BÀI CHI TIẾT")
    with_content = build_context([a], [a], k_deep=1, index_limit=60, include_content=True)
    without = build_context([a], [a], k_deep=1, index_limit=60, include_content=False)

    assert "THÂN BÀI CHI TIẾT" in with_content.deep_block
    assert "THÂN BÀI CHI TIẾT" not in without.deep_block
    # 7 field phân tích vẫn còn ở cả hai — đó là phần đủ cho câu SO SÁNH (đo 28/07).
    assert "Vì sao A quan trọng" in without.deep_block


def test_hidden_counts_only_ranked_tail():
    """Refs đến từ ngoài tập xếp hạng không được tính vào "còn N tin khác"."""
    outside = _FakeInsight("Ngoài cửa sổ")
    ranked = [_FakeInsight(t) for t in "ABCDE"]
    ctx = build_context([outside], ranked, k_deep=2, index_limit=3)

    # 1 ô sâu ngoài + 1 ô sâu từ ranked + 1 index = 2 tin của `ranked` được rót
    assert ctx.total_matched == 5
    assert ctx.hidden == 3


# --- history markers ---------------------------------------------------------------------


def test_history_markers_become_titles():
    """`[3]` lượt trước và `[3]` lượt này là hai tin khác nhau — phải giải thành tên."""
    history = [
        _Turn("user", "tin nào về Kubernetes?"),
        _Turn("assistant", "Có bản vá khẩn [3].", [_Cit(3, "Kubernetes CVE chưa vá")]),
    ]
    block = _history_block(history)

    assert "[«Kubernetes CVE chưa vá»]" in block
    assert "[3]" not in block


def test_history_marker_without_citation_is_dropped():
    """Client cũ không gửi citations → con số vô nghĩa còn tệ hơn không có gì."""
    block = _history_block([_Turn("assistant", "Có bản vá khẩn [3].")])

    assert "[3]" not in block
    assert "Có bản vá khẩn" in block


# --- đường refs qua ChatService -----------------------------------------------------------


class _FakeGemini:
    def __init__(self, answer="Đối chiếu hai tin [1][2]."):
        self.answer = answer
        self.prompts = []

    def chat(self, system_prompt, user_prompt, state=None):
        self.prompts.append(user_prompt)
        return self.answer, 1


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return self._value


class _FakeSession:
    """Trả quota trước, rồi trả tập insight cho `_load_refs`."""

    def __init__(self, refs, quota_used=0):
        self._refs = refs
        self._quota = quota_used
        self._seen_quota = False
        self.added = []

    async def execute(self, statement, *a, **kw):
        if not self._seen_quota:
            self._seen_quota = True
            return _Result(self._quota)
        return _Result(self._refs)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass


def _service(candidates, refs_in_db, gemini=None):
    session = _FakeSession(refs_in_db)
    service = ChatService(session, gemini=gemini or _FakeGemini())

    async def fake_list_for_chat(**kw):
        return candidates

    service.insight_repo.list_for_chat = fake_list_for_chat
    return service


@pytest.mark.asyncio
async def test_refs_give_mode_focused_in_one_call():
    a, b = _FakeInsight("Gemma 4"), _FakeInsight("DiffusionGemma")
    gemini = _FakeGemini()
    service = _service([a, b], [a, b], gemini)

    result = await service.answer(
        "so sánh hai cái này", [], None, referenced_insight_ids=[a.id, b.id]
    )

    assert result["mode"] == "focused"
    assert service._steps_used == 1, "đường refs KHÔNG dùng sentinel/mở rộng"
    assert "LUẬT TRÌNH BÀY" in gemini.prompts[0], "≥2 ô sâu phải mở khoá hình dạng đối chiếu"


@pytest.mark.asyncio
async def test_dead_ref_is_skipped_silently():
    """Ghim một tin rồi tin đó bị unpublish — không được làm hỏng cả câu hỏi (D7)."""
    a = _FakeInsight("Còn sống")
    gemini = _FakeGemini(answer="Trả lời [1].")
    service = _service([a], [a], gemini)

    result = await service.answer(
        "hỏi gì đó", [], None, referenced_insight_ids=[a.id, uuid.uuid4()]
    )

    assert result["mode"] == "focused"
    assert result["citations"][0]["title"] == "Còn sống"


@pytest.mark.asyncio
async def test_all_refs_dead_falls_back_to_global():
    """Không ref nào còn sống ⇒ không có ô sâu do người dùng chọn ⇒ đây là câu toàn cục."""
    a = _FakeInsight("Tin A")
    service = _service([a], [], _FakeGemini(answer="Trả lời [1]."))

    result = await service.answer(
        "hỏi gì đó", [], None, referenced_insight_ids=[uuid.uuid4()]
    )

    assert result["mode"] == "global"


@pytest.mark.asyncio
async def test_no_refs_behaves_exactly_like_before():
    a = _FakeInsight("Tin A")
    service = _service([a], [], _FakeGemini(answer="Trả lời [1]."))

    result = await service.answer("có gì mới?", [], None)

    assert result["mode"] == "global"
    assert result["citations"][0]["title"] == "Tin A"


# --- Bất biến D4 trên lối vào MỚI (W1) ---------------------------------------------------


@pytest.mark.asyncio
async def test_focused_prompt_contains_no_uuid():
    """Đường `focused` là lối vào MỚI nhận UUID từ client — prompt vẫn không được chứa nó.

    `test_index_reaches_prompt_without_uuid` canh đường toàn cục, nhưng đường refs mới là
    đường mà client tự khai định danh. Cơ chế chống bịa citation là **cấu trúc** (server cấp
    số, model chỉ đánh dấu), nên một lối vào không có ai canh là chỗ nó có thể vỡ trong im
    lặng: model không bao giờ nhìn thấy UUID thì không có gì để bịa.

    Cũng khẳng định định danh KHÔNG rò sang phép tính từ khoá — nhét id/URL vào text câu hỏi
    vừa phá bất biến này vừa làm nhiễu `_relevance`, đó là lý do refs đi bằng field riêng.
    """
    from app.services.chat_service import _question_terms

    picked = [_FakeInsight("Gemma 4"), _FakeInsight("DiffusionGemma")]
    others = [_FakeInsight(f"Tin {i}") for i in range(5)]
    gemini = _FakeGemini()
    service = _service(picked + others, picked, gemini)

    question = "so sánh hai cái này"
    await service.answer(
        question, [], None, referenced_insight_ids=[i.id for i in picked]
    )

    prompt = gemini.prompts[0]
    leaked = [str(i.id) for i in picked + others if str(i.id) in prompt]
    assert leaked == [], f"UUID rò vào prompt — model sẽ bịa được id: {leaked[:3]}"
    assert not any(str(i.id) in " ".join(_question_terms(question)) for i in picked)


@pytest.mark.asyncio
async def test_refs_over_cap_are_truncated_not_rejected(monkeypatch):
    """Gửi thừa tham chiếu → lấy phần đầu, KHÔNG lỗi (design D7).

    Cắt ở server chứ không tin client tự cắt: widget và `chat_deep_slots` là hai nguồn sự
    thật khác nhau, và lệch số chỉ được phép làm UI hiện thừa vài chip — không được làm
    prompt phình quá ngân sách.
    """
    monkeypatch.setattr("app.services.chat_service.settings.chat_deep_slots", 3)
    picked = [_FakeInsight(f"Ghim {i}") for i in range(5)]
    gemini = _FakeGemini(answer="Trả lời [1].")
    service = _service(picked, picked, gemini)

    result = await service.answer(
        "hỏi gì đó", [], None, referenced_insight_ids=[i.id for i in picked]
    )

    assert result["mode"] == "focused"
    # Nhãn `Vì sao quan trọng:` chỉ do `build_insight_block` sinh ra, không có trong dòng
    # index nén ⇒ đếm nhãn là đếm số ô sâu thật sự vào prompt. (Đếm "Vì sao" trần thì trúng
    # cả GIÁ TRỊ của field — 2 lần mỗi khối.)
    assert gemini.prompts[0].count("Vì sao quan trọng:") == 3
    # Hai tin dư vẫn còn quyền cạnh tranh ở index, không bị vứt khỏi context.
    assert "Ghim 4" in gemini.prompts[0]
