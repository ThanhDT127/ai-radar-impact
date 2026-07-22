"""ChatService chế độ A (toàn cục) — retrieval do server điều khiển.

Bất biến cần khoá: model KHÔNG chọn điều kiện truy vấn và KHÔNG thấy UUID; index rỗng
phải dẫn tới "không tìm thấy" chứ không phải bịa; xếp hạng dùng lại `score_for_role`
của delivery chứ không tự chế tiêu chí.
"""

import uuid
from datetime import datetime

import pytest

from app.services.chat_grounding import INSUFFICIENT_GROUNDS_MESSAGE
from app.services.chat_service import ChatService


class _FakeInsight:
    def __init__(self, title, role_urgency="medium", roles=None, impact="Trung bình"):
        self.id = uuid.uuid4()
        self.title = title
        self.signal = f"Ý nghĩa của {title}"
        self.so_what = f"Nên làm gì với {title}"
        self.summary_short = "ngắn"
        self.summary_medium = "vừa"
        self.affected_roles = roles or ["Security"]
        self.topics = ["Security & Compliance"]
        self.source_url = f"https://example.com/{title}"
        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.impact_label = impact
        self.actionability_score = 0.5
        self.intelligence_tier = "Tactical"
        self.trust_score = 0.8
        self.practical_indicators = None
        self.recommendations = {
            r: {"action_type": "read", "note": "n", "urgency": role_urgency}
            for r in (roles or ["Security"])
        }


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeSession:
    def __init__(self, quota_used=0):
        self._results = [_Result(quota_used)]
        self.added = []

    async def execute(self, statement, *a, **kw):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass


class _FakeGemini:
    def __init__(self, answer="Có tin này [1]."):
        self.answer = answer
        self.prompts = []

    def chat(self, system_prompt, user_prompt):
        self.prompts.append(user_prompt)
        return self.answer, 1


def _service(candidates, gemini=None, quota_used=0):
    session = _FakeSession(quota_used)
    service = ChatService(session, gemini=gemini or _FakeGemini())

    async def fake_list_for_chat(**kw):
        return candidates

    service.insight_repo.list_for_chat = fake_list_for_chat
    return service, session


@pytest.mark.asyncio
async def test_index_reaches_prompt_without_uuid():
    items = [_FakeInsight("Tin A"), _FakeInsight("Tin B")]
    gemini = _FakeGemini()
    service, _ = _service(items, gemini)

    await service.answer("Có gì mới không?", [], None)

    prompt = gemini.prompts[0]
    assert "Tin A" in prompt and "Tin B" in prompt
    for item in items:
        assert str(item.id) not in prompt, "UUID rò vào prompt — model sẽ bịa được id"


@pytest.mark.asyncio
async def test_empty_index_says_not_found_without_fabricating():
    gemini = _FakeGemini(answer="Không tìm thấy thông tin này trong hệ thống.")
    service, _ = _service([], gemini)

    result = await service.answer("Có tin gì về blockchain không?", [], None)

    assert "không có tin nào" in gemini.prompts[0].lower()
    assert result["citations"] == []
    assert result["answer"].startswith("Không tìm thấy")


@pytest.mark.asyncio
async def test_empty_index_with_fabricated_answer_is_blocked():
    """Index rỗng mà model vẫn khẳng định → fail-closed chặn lại."""
    gemini = _FakeGemini(answer="Có, tuần này Google ra mắt Gemini 4.")
    service, _ = _service([], gemini)

    result = await service.answer("Có gì mới?", [], None)

    assert result["answer"] == INSUFFICIENT_GROUNDS_MESSAGE


@pytest.mark.asyncio
async def test_ranking_puts_high_role_urgency_first():
    """Xếp hạng dùng `score_for_role` — urgency vai trò là trục đầu tiên."""
    low = _FakeInsight("Tin thường", role_urgency="low")
    high = _FakeInsight("Tin khẩn", role_urgency="high")
    gemini = _FakeGemini()
    service, _ = _service([low, high], gemini)

    await service.answer("Security cần chú ý gì?", [], None)

    prompt = gemini.prompts[0]
    assert prompt.index("Tin khẩn") < prompt.index("Tin thường")


@pytest.mark.asyncio
async def test_role_without_high_urgency_still_gets_full_index():
    """Bài học 21/07: xếp hạng, KHÔNG lọc ngưỡng.

    Data Scientist có 0 entry `high` trên corpus thật — lọc theo ngưỡng sẽ trả rỗng
    cho vai trò này dù dữ liệu có tin liên quan.
    """
    items = [
        _FakeInsight("Tin DS 1", role_urgency="medium", roles=["Data Scientist"]),
        _FakeInsight("Tin DS 2", role_urgency="low", roles=["Data Scientist"]),
    ]
    gemini = _FakeGemini()
    service, _ = _service(items, gemini)

    await service.answer("Data Scientist có gì đáng đọc?", [], None)

    prompt = gemini.prompts[0]
    assert "Tin DS 1" in prompt and "Tin DS 2" in prompt, "không được lọc bớt vì urgency thấp"


@pytest.mark.asyncio
async def test_role_with_zero_data_is_stated_explicitly():
    """`Data Analyst` có 0 entry trên corpus thật — phải nói ra, không im lặng."""
    items = [_FakeInsight("Tin bảo mật", roles=["Security"])]
    gemini = _FakeGemini()
    service, _ = _service(items, gemini)

    await service.answer("Data Analyst cần chú ý gì?", [], None)

    prompt = gemini.prompts[0]
    assert "KHÔNG có tin nào ảnh hưởng tới vai trò Data Analyst" in prompt


@pytest.mark.asyncio
async def test_role_with_data_gets_no_empty_notice():
    items = [_FakeInsight("Tin bảo mật", roles=["Security"])]
    gemini = _FakeGemini()
    service, _ = _service(items, gemini)

    await service.answer("Security cần chú ý gì?", [], None)

    assert "KHÔNG có tin nào ảnh hưởng" not in gemini.prompts[0]


@pytest.mark.asyncio
async def test_relevance_beats_importance_in_ranking(monkeypatch):
    """Độ liên quan tới câu hỏi phải đứng TRƯỚC độ quan trọng chung.

    Hồi quy cho lỗi đo 22/07: xếp hạng chỉ theo `score_for_role` (mù với câu hỏi) làm
    recall tin liên quan rớt còn 42% khi cắt top-K — tin chủ đề ngách thường urgency
    thấp nên nằm hết ở đuôi và bị cắt sạch, mà model vẫn trả lời trôi chảy từ phần sót.
    """
    monkeypatch.setattr('app.services.chat_service.settings.chat_index_top_k', 1)
    urgent_unrelated = _FakeInsight("Lỗ hổng nghiêm trọng Fortinet", role_urgency="high")
    relevant_calm = _FakeInsight("Mô hình mã nguồn mở Llama", role_urgency="low")
    gemini = _FakeGemini()
    service, _ = _service([urgent_unrelated, relevant_calm], gemini)

    await service.answer("Có tin nào về mã nguồn mở không?", [], None)

    prompt = gemini.prompts[0]
    assert "mã nguồn mở" in prompt.lower()
    assert "Fortinet" not in prompt, "tin khẩn nhưng lạc đề không được chiếm chỗ"


@pytest.mark.asyncio
async def test_ranking_falls_back_to_importance_without_keywords(monkeypatch):
    """Câu hỏi chung chung (toàn stopword) → quay về xếp theo độ quan trọng."""
    monkeypatch.setattr('app.services.chat_service.settings.chat_index_top_k', 1)
    low = _FakeInsight("Tin thường", role_urgency="low")
    high = _FakeInsight("Tin khẩn", role_urgency="high")
    gemini = _FakeGemini()
    service, _ = _service([low, high], gemini)

    await service.answer("Có gì mới không?", [], None)

    assert "Tin khẩn" in gemini.prompts[0]


@pytest.mark.asyncio
async def test_index_capped_at_top_k(monkeypatch):
    """Cắt top-K sau xếp hạng — đo 22/07: 179→60 tin giảm 44% chi phí, 35% thời gian."""
    monkeypatch.setattr('app.services.chat_service.settings.chat_index_top_k', 3)
    items = [_FakeInsight(f"Tin {i}") for i in range(10)]
    gemini = _FakeGemini()
    service, _ = _service(items, gemini)

    await service.answer("Có gì mới?", [], None)

    prompt = gemini.prompts[0]
    assert "[3]" in prompt and "[4]" not in prompt, "phải cắt đúng 3 tin"
    assert "còn 7 tin nữa" in prompt, "phải cho model biết tổng thật để đếm đúng"


@pytest.mark.asyncio
async def test_role_with_data_below_cutoff_is_not_reported_empty(monkeypatch):
    """Bẫy của top-K: vai trò có tin nhưng xếp hạng dưới ngưỡng.

    Nếu tính `empty_roles` SAU khi cắt thì bot sẽ nói "chưa có tin nào cho Data
    Scientist" trong khi hệ thống có — sai nghiêm trọng hơn việc không nhắc tới.
    """
    monkeypatch.setattr('app.services.chat_service.settings.chat_index_top_k', 2)
    items = [
        _FakeInsight("Tin bảo mật 1", role_urgency="high", roles=["Security"]),
        _FakeInsight("Tin bảo mật 2", role_urgency="high", roles=["Security"]),
        _FakeInsight("Tin DS", role_urgency="low", roles=["Data Scientist"]),
    ]
    gemini = _FakeGemini()
    service, _ = _service(items, gemini)

    await service.answer("Data Scientist có gì đáng đọc?", [], None)

    assert "KHÔNG có tin nào ảnh hưởng" not in gemini.prompts[0]


@pytest.mark.asyncio
async def test_top_k_zero_means_no_cap(monkeypatch):
    monkeypatch.setattr('app.services.chat_service.settings.chat_index_top_k', 0)
    items = [_FakeInsight(f"Tin {i}") for i in range(8)]
    gemini = _FakeGemini()
    service, _ = _service(items, gemini)

    await service.answer("Có gì mới?", [], None)

    assert "[8]" in gemini.prompts[0]
    assert "tin nữa xếp hạng thấp hơn" not in gemini.prompts[0]


@pytest.mark.asyncio
async def test_mode_is_global_and_logged():
    service, session = _service([_FakeInsight("Tin A")])
    result = await service.answer("?", [], None)

    assert result["mode"] == "global"
    assert session.added[0].mode == "global"
    assert session.added[0].model_calls == 1
