"""Định tuyến ý định (fast‑path chào hỏi/meta) — change `chat-intent-router`.

Bất biến khoá: câu chào/meta/cảm ơn trả preset với **0 lượt gọi model**, `mode="meta"`,
KHÔNG tiêu và KHÔNG bị chặn bởi quota; còn câu có nội dung thực chất (kể cả khi có tiền tố
chào) SHALL fall‑through vào pipeline. False‑positive (gạt nhầm câu thật) tệ hơn nhiều
false‑negative, nên phân loại thiên hẳn về fall‑through (design D2).
"""

import uuid

import pytest

from app.config import settings
from app.services.chat_intent import INTENT_PRESETS, classify_intent
from app.services.chat_service import ChatService, QuotaExceededError


# --- Nhóm 1: phân loại thuần (deterministic, không chạm DB/model) -----------------

@pytest.mark.parametrize(
    "question,expected",
    [
        # fast‑path — DoD 1.1
        ("chào bạn", "salutation"),
        ("xin chào", "salutation"),
        ("hello", "salutation"),
        ("cảm ơn nhé", "thanks"),
        ("cảm ơn", "thanks"),
        ("thanks", "thanks"),
        ("bạn làm được gì", "capability"),
        ("bạn làm được gì?", "capability"),
        ("bạn là ai", "capability"),
        ("chào bạn, làm được gì?", "capability"),  # tiền tố chào + câu năng lực
        # fall‑through — câu có nội dung thực chất → None (task 3.1)
        ("chào, tuần này có gì cho Security", None),
        ("cảm ơn vì tin về mã nguồn mở", None),
        ("OpenSSL là gì", None),  # "là gì" nhưng còn "openssl" → không được gạt
        ("tuần này có gì cho Dev", None),
        ("rủi ro của nó là gì", None),
    ],
)
def test_classify_intent(question, expected):
    assert classify_intent(question) == expected


def test_no_preset_is_empty():
    """DoD 1.2 — mỗi nhóm có một preset, không nhóm nào trả chuỗi rỗng."""
    for group in ("salutation", "capability", "thanks"):
        assert INTENT_PRESETS[group].strip()
    # Preset năng lực phải ĐIỀU HƯỚNG: nêu ví dụ truy vấn (design D4).
    assert "?" in INTENT_PRESETS["capability"]


# --- Fakes cho tầng service (không có hạ tầng DB test) ---------------------------

class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.added = []
        self.commits = 0

    async def execute(self, statement, *a, **kw):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1


class _FakeGemini:
    def __init__(self, answer="Câu trả lời có căn cứ [1].", calls=1):
        self.answer = answer
        self.calls = calls
        self.prompts = []

    def chat(self, system_prompt, user_prompt):
        self.prompts.append((system_prompt, user_prompt))
        return self.answer, self.calls


# --- Nhóm 2: fast‑path ở tầng service --------------------------------------------

@pytest.mark.asyncio
async def test_fastpath_returns_meta_without_calling_model():
    """Task 3.2 + 3.4 — chào → mode meta, citations rỗng, 0 lượt gọi model, log 0."""
    gemini = _FakeGemini()
    session = _FakeSession([])  # fast‑path không truy vấn gì
    service = ChatService(session, gemini=gemini)

    result = await service.answer("xin chào", [], None)

    assert result["mode"] == "meta"
    assert result["citations"] == []
    assert result["answer"] == INTENT_PRESETS["salutation"]
    assert gemini.prompts == [], "fast‑path KHÔNG được gọi Gemini"
    assert session.added, "vẫn ghi chat_logs để đo tần suất"
    assert session.added[0].model_calls == 0, "log 0 → không đội budget"
    assert session.added[0].mode == "meta"


@pytest.mark.asyncio
async def test_fastpath_capability_calls_no_model():
    gemini = _FakeGemini()
    service = ChatService(_FakeSession([]), gemini=gemini)

    result = await service.answer("bạn làm được gì?", [], None)

    assert result["mode"] == "meta"
    assert result["answer"] == INTENT_PRESETS["capability"]
    assert gemini.prompts == []


@pytest.mark.asyncio
async def test_fastpath_applies_even_with_insight_id():
    """Task 2.4 — chào kèm insight_id → preset, KHÔNG nạp bài gốc, KHÔNG gọi model."""
    gemini = _FakeGemini()
    # Nếu fast‑path lỡ nạp insight, nó sẽ execute() và làm cạn hàng đợi này.
    session = _FakeSession([_Result(object())])
    service = ChatService(session, gemini=gemini)

    result = await service.answer("chào bạn", [], uuid.uuid4())

    assert result["mode"] == "meta"
    assert gemini.prompts == []
    assert len(session._results) == 1, "không được nạp bài gốc (execute chưa chạy)"


@pytest.mark.asyncio
async def test_fallthrough_real_question_calls_model():
    """Task 3.1 — 'chào, tuần này có gì cho Security' KHÔNG bị fast‑path → đi pipeline."""
    gemini = _FakeGemini()
    insight = _FakeInsightLike()
    session = _FakeSession([_Result(0), _Result(insight)])  # quota, load insight
    service = ChatService(session, gemini=gemini)

    result = await service.answer(
        "chào, tuần này có gì cho Security", [], insight.id
    )

    assert result["mode"] == "insight", "câu thật đi đúng chế độ cũ, không phải meta"
    assert gemini.prompts, "câu thật phải gọi model đúng 1 lần"


# --- Nhóm 3: tương tác với quota (design D3) -------------------------------------

@pytest.mark.asyncio
async def test_fastpath_not_blocked_when_quota_exhausted():
    """Task 3.3 (nhánh chào) — budget cạn + chào → vẫn preset, không 429, không check quota."""
    gemini = _FakeGemini()
    # Đặt sẵn kết quả quota "đã cạn"; fast‑path KHÔNG được đụng tới nó.
    session = _FakeSession([_Result(settings.max_daily_chat_calls)])
    service = ChatService(session, gemini=gemini)

    result = await service.answer("xin chào", [], None)

    assert result["mode"] == "meta"
    assert len(session._results) == 1, "fast‑path không được kiểm quota"
    assert session.added[0].model_calls == 0


@pytest.mark.asyncio
async def test_real_question_still_429_when_quota_exhausted():
    """Task 3.3 (nhánh câu thật) — budget cạn + câu thật → 429."""
    gemini = _FakeGemini()
    session = _FakeSession([_Result(settings.max_daily_chat_calls)])
    service = ChatService(session, gemini=gemini)

    with pytest.raises(QuotaExceededError):
        await service.answer("tuần này có gì cho Security", [], None)

    assert gemini.prompts == []


class _FakeSourceLike:
    name = "Test Source"


class _FakeRawDocLike:
    normalized_content = "Nội dung bài gốc rất dài về bảo mật Security."
    source = _FakeSourceLike()


class _FakeInsightLike:
    """Insight tối thiểu đủ cho chế độ B đi qua grounding."""

    def __init__(self):
        self.id = uuid.uuid4()
        self.title = "Tin thử nghiệm về Security"
        self.signal = "Ý nghĩa cô đọng"
        self.summary_short = "ngắn"
        self.summary_medium = "vừa"
        self.why_it_matters = "quan trọng"
        self.so_what = "nên làm gì đó"
        self.risks = ["rủi ro A"]
        self.recommendations = {"Security": {"action_type": "read", "note": "đọc"}}
        self.affected_roles = ["Security"]
        self.topics = ["Security & Compliance"]
        self.source_url = "https://example.com/a"
        from datetime import datetime

        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.raw_document = _FakeRawDocLike()
