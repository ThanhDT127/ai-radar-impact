"""ChatService chế độ B — với GeminiClient mock (không gọi Vertex thật).

Suite không có hạ tầng DB test (xem `test_insight_count_queries.py`), nên session được
giả bằng hàng đợi kết quả theo đúng thứ tự service truy vấn:
  1. đếm budget đã dùng trong ngày
  2. load insight
"""

import uuid
from datetime import datetime

import pytest

from app.config import settings
from app.services.chat_grounding import INSUFFICIENT_GROUNDS_MESSAGE
from app.services.chat_service import (
    ChatService,
    InsightNotFoundError,
    QuotaExceededError,
)


class _FakeSource:
    name = "Test Source"


class _FakeRawDoc:
    def __init__(self, content="Nội dung bài gốc rất dài về IoT."):
        self.normalized_content = content
        self.source = _FakeSource()


class _FakeInsight:
    def __init__(self, content="Nội dung bài gốc rất dài về IoT."):
        self.id = uuid.uuid4()
        self.title = "Tin thử nghiệm"
        self.signal = "Ý nghĩa cô đọng"
        self.summary_short = "ngắn"
        self.summary_medium = "vừa"
        self.why_it_matters = "quan trọng vì X"
        self.so_what = "nên làm Y"
        self.risks = ["rủi ro A"]
        self.recommendations = {"Dev": {"action_type": "read", "note": "đọc"}}
        self.affected_roles = ["Dev"]
        self.topics = ["AI/ML Ứng dụng"]
        self.source_url = "https://example.com/a"
        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.raw_document = _FakeRawDoc(content)


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    """Trả kết quả theo hàng đợi; ghi lại bản ghi log đã add."""

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
    """Đứng thay GeminiClient — ghi lại prompt để soi, trả câu trả lời dựng sẵn."""

    def __init__(self, answer="Câu trả lời có căn cứ [1].", calls=1):
        self.answer = answer
        self.calls = calls
        self.prompts = []

    def chat(self, system_prompt, user_prompt):
        self.prompts.append((system_prompt, user_prompt))
        return self.answer, self.calls


def _service(insight=None, quota_used=0, gemini=None):
    results = [_Result(quota_used)]
    if insight is not None or insight is None:
        results.append(_Result(insight))
    session = _FakeSession(results)
    return ChatService(session, gemini=gemini or _FakeGemini()), session


@pytest.mark.asyncio
async def test_happy_path_returns_answer_and_citation():
    insight = _FakeInsight()
    service, session = _service(insight)

    result = await service.answer("Tin này nói gì?", [], insight.id)

    assert result["mode"] == "insight"
    assert result["answer"] == "Câu trả lời có căn cứ [1]."
    assert len(result["citations"]) == 1
    assert result["citations"][0]["insight_id"] == insight.id
    assert session.added[0].model_calls == 1, "phải ghi log lượt gọi đã dùng"
    assert session.added[0].mode == "insight"


@pytest.mark.asyncio
async def test_original_article_reaches_the_prompt():
    """Lý do tồn tại của chế độ B — bài gốc phải thực sự vào context."""
    insight = _FakeInsight(content="Chi tiết chỉ có trong bài gốc: cổng UART 115200.")
    gemini = _FakeGemini()
    service, _ = _service(insight, gemini=gemini)

    await service.answer("Baud rate bao nhiêu?", [], insight.id)

    _, user_prompt = gemini.prompts[0]
    assert "UART 115200" in user_prompt
    assert str(insight.id) not in user_prompt, "UUID không được vào prompt (D4)"


@pytest.mark.asyncio
async def test_missing_insight_raises_before_calling_model():
    gemini = _FakeGemini()
    service, session = _service(None, gemini=gemini)

    with pytest.raises(InsightNotFoundError):
        await service.answer("Hỏi gì đó", [], uuid.uuid4())

    assert gemini.prompts == [], "không được gọi Gemini khi insight không tồn tại"
    assert session.added == [], "không tốn lượt gọi thì không ghi log"


@pytest.mark.asyncio
async def test_quota_exceeded_blocks_before_calling_model():
    gemini = _FakeGemini()
    session = _FakeSession([_Result(settings.max_daily_chat_calls)])
    service = ChatService(session, gemini=gemini)

    with pytest.raises(QuotaExceededError):
        await service.answer("Hỏi gì đó", [], None)

    assert gemini.prompts == []


@pytest.mark.asyncio
async def test_out_of_range_marker_dropped_answer_kept():
    insight = _FakeInsight()
    gemini = _FakeGemini(answer="Điều này đúng [1], điều kia [7] cũng thế.")
    service, _ = _service(insight, gemini=gemini)

    result = await service.answer("?", [], insight.id)

    assert "[7]" not in result["answer"]
    assert "điều kia" in result["answer"]
    assert len(result["citations"]) == 1


@pytest.mark.asyncio
async def test_unsourced_answer_is_failed_closed():
    insight = _FakeInsight()
    gemini = _FakeGemini(answer="Gemini 3 vừa ra mắt và mạnh hơn nhiều.")
    service, session = _service(insight, gemini=gemini)

    result = await service.answer("?", [], insight.id)

    assert result["answer"] == INSUFFICIENT_GROUNDS_MESSAGE
    assert result["citations"] == []
    assert session.added[0].citations_count == 0


@pytest.mark.asyncio
async def test_not_found_answer_passes_without_citation():
    insight = _FakeInsight()
    gemini = _FakeGemini(answer="Không tìm thấy thông tin này trong hệ thống.")
    service, _ = _service(insight, gemini=gemini)

    result = await service.answer("?", [], insight.id)

    assert result["answer"] == "Không tìm thấy thông tin này trong hệ thống."
    assert result["citations"] == []


@pytest.mark.asyncio
async def test_purged_original_still_answers_with_insight_fields():
    """Tombstone-purge xoá bài gốc nhưng insight còn sống."""
    insight = _FakeInsight(content="")
    gemini = _FakeGemini()
    service, _ = _service(insight, gemini=gemini)

    result = await service.answer("Chi tiết trong bài?", [], insight.id)

    _, user_prompt = gemini.prompts[0]
    assert "hết hạn lưu trữ" in user_prompt
    assert "Ý nghĩa cô đọng" in user_prompt, "vẫn phải gửi các trường insight"
    assert result["citations"], "vẫn trả lời được, không lỗi"


@pytest.mark.asyncio
async def test_log_written_even_when_step_after_model_fails(monkeypatch):
    """Lượt gọi đã trả về = đã tốn tiền → phải vào budget dù request vỡ sau đó."""
    insight = _FakeInsight()
    gemini = _FakeGemini()
    service, session = _service(insight, gemini=gemini)

    def boom(*a, **kw):
        raise RuntimeError("vỡ sau khi gọi model")

    monkeypatch.setattr("app.services.chat_service.resolve_citations", boom)

    with pytest.raises(RuntimeError):
        await service.answer("?", [], insight.id)

    assert session.added, "chat_logs phải được ghi trong finally"
    assert session.added[0].model_calls == 1


@pytest.mark.asyncio
async def test_history_reaches_prompt():
    from app.schemas.chat import ChatTurn

    insight = _FakeInsight()
    gemini = _FakeGemini()
    service, _ = _service(insight, gemini=gemini)

    history = [
        ChatTurn(role="user", content="Câu hỏi trước"),
        ChatTurn(role="assistant", content="Trả lời trước"),
    ]
    await service.answer("Còn rủi ro thì sao?", history, insight.id)

    _, user_prompt = gemini.prompts[0]
    assert "Câu hỏi trước" in user_prompt
    assert "Trả lời trước" in user_prompt
