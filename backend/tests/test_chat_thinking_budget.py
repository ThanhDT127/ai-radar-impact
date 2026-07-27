"""Ngân sách suy luận của chat (`chat-latency-thinking-budget`) — CƠ CHẾ, không phải tốc độ.

File này KHÔNG đo giây: độ trễ phụ thuộc mạng và tải của Vertex nên đo trong unit test là
tạo ra một test bập bênh. Nó khoá những thứ tất định và **im lặng khi hỏng**:

  - cấu hình suy luận có mặt ở CẢ `chat()` lẫn `chat_stream()` (hai lối ra không được trôi
    khỏi nhau — cổng chất lượng chỉ đi lối blocking);
  - `gate_analyze`/`analyze`/`classify_intent` KHÔNG bị áp ngân sách này;
  - câu rỗng từ khoá không tiêu một lượt embed nào;
  - `None` (không đo được) và `0` (đã ghìm) không bị gộp làm một.

Số đo tốc độ nằm ở `openspec/changes/chat-latency-thinking-budget/measurement.md`.
"""

import uuid
from datetime import datetime

import pytest

from app.ai import gemini_client as gc
from app.config import settings


# --- Cấu hình suy luận dựng ở một chỗ -----------------------------------------------


def test_chat_config_carries_thinking_budget():
    settings.chat_thinking_budget = 256
    config = gc._chat_generation_config("hệ thống")

    assert config.thinking_config is not None
    assert config.thinking_config.thinking_budget == 256


def test_budget_minus_one_means_let_model_decide():
    """`-1` = hành vi TRƯỚC change này. Đây là đường lùi khi cần so sánh lại."""
    settings.chat_thinking_budget = -1
    try:
        assert gc._chat_generation_config("hệ thống").thinking_config is None
    finally:
        settings.chat_thinking_budget = 256


def test_budget_zero_is_configured_not_omitted():
    """`0` phải ĐƯỢC GỬI ĐI (tắt hẳn suy luận), không được lẫn với "không đặt gì"."""
    settings.chat_thinking_budget = 0
    try:
        config = gc._chat_generation_config("hệ thống")
        assert config.thinking_config is not None
        assert config.thinking_config.thinking_budget == 0
    finally:
        settings.chat_thinking_budget = 256


def test_both_chat_paths_use_the_same_config_builder():
    """Bất biến D3: một chỗ dựng config cho cả hai lối ra.

    Nếu ai đó viết `types.GenerateContentConfig(...)` thẳng trong `_chat_once` hoặc
    `_chat_stream_once` thì bản blocking và bản streaming trả lời khác nhau **im lặng** —
    mà `chat_answer_harness` chỉ đi lối blocking, nên cổng chất lượng sẽ gác nhầm cấu hình.
    """
    import inspect

    for fn in (gc.GeminiClient._chat_once, gc.GeminiClient._chat_stream_once):
        source = inspect.getsource(fn)
        assert "_chat_generation_config(" in source, f"{fn.__name__} phải dùng builder chung"
        assert "GenerateContentConfig(" not in source, (
            f"{fn.__name__} tự dựng config riêng — hai lối ra sẽ trôi khỏi nhau"
        )


def test_analysis_paths_do_not_get_chat_thinking_budget():
    """Gate/analyze/intent là tác vụ NỀN — độ trễ không nằm trên đường phục vụ người dùng.

    Áp ngân sách chat cho chúng nghĩa là phải chạy lại benchmark gate 54 doc và chấp nhận
    rủi ro accuracy 94% / recall 100% tụt. Ngoài phạm vi change này (proposal Non-goals).
    """
    import inspect

    for fn in (
        gc.GeminiClient.gate_analyze,
        gc.GeminiClient.analyze,
        gc.GeminiClient.classify_intent,
    ):
        # Soi CODE, không soi docstring: `classify_intent` có nhắc chữ "thinking" trong phần
        # giải thích vì sao không dùng được `gemini-2.5-flash` — đó là tài liệu, không phải
        # cấu hình. Bắt theo tên thuộc tính thật (`thinking_config`) mới là kiểm đúng thứ cần.
        source = inspect.getsource(fn)
        code = source.replace(inspect.getdoc(fn) or "", "")
        assert "thinking_config" not in code, f"{fn.__name__} không được nhận thinking config"
        assert "ThinkingConfig" not in code
        assert "_chat_generation_config" not in code


# --- Đọc số token suy luận ----------------------------------------------------------


class _Usage:
    def __init__(self, thoughts):
        self.thoughts_token_count = thoughts


class _Response:
    def __init__(self, thoughts=None, has_usage=True):
        self.usage_metadata = _Usage(thoughts) if has_usage else None


def test_thinking_tokens_read_from_usage():
    assert gc._thinking_tokens(_Response(253)) == 253


def test_thinking_tokens_none_when_provider_silent():
    """SDK 0.8.0 luôn trả rỗng — đúng lý do chi phí này ẩn được 5 ngày. Không được biến
    thành `0`, vì `0` nghĩa là "đã ghìm và model tuân thủ"."""
    assert gc._thinking_tokens(_Response(None)) is None
    assert gc._thinking_tokens(_Response(has_usage=False)) is None
    assert gc._thinking_tokens(object()) is None


def test_state_accumulates_across_retry():
    """Lượt hỏi lại chống-cắt cũng tốn tiền thật ⇒ phải cộng dồn, không ghi đè."""
    state = gc.ChatStreamState()
    state.add_thinking(200)
    state.add_thinking(150)
    assert state.thinking_tokens == 350


def test_state_keeps_none_when_never_measured():
    state = gc.ChatStreamState()
    state.add_thinking(None)
    assert state.thinking_tokens is None


# --- Câu rỗng từ khoá không tiêu lượt embed -----------------------------------------


class _FakeInsight:
    def __init__(self, title):
        self.id = uuid.uuid4()
        self.title = title
        self.signal = "tín hiệu"
        self.so_what = ""
        self.summary_short = ""
        self.summary_medium = "vừa"
        self.affected_roles = ["Security"]
        self.topics = ["Security & Compliance"]
        self.source_url = "https://example.com/a"
        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.impact_label = "Cao"
        self.actionability_score = 0.5
        self.intelligence_tier = "Tactical"
        self.trust_score = 0.8
        self.practical_indicators = None
        self.embedding = None
        self.recommendations = {
            "Security": {"action_type": "read", "note": "n", "urgency": "high"}
        }


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeSession:
    def __init__(self):
        self._results = [_Result(0)]

    async def execute(self, statement, *a, **kw):
        return self._results.pop(0)

    def add(self, obj):
        pass

    async def commit(self):
        pass


class _FakeGemini:
    def __init__(self):
        self.embed_calls = 0
        self.thinking = 111

    def chat(self, system_prompt, user_prompt, state=None):
        if state is not None:
            state.add_thinking(self.thinking)
        return "Câu trả lời [1].", 1

    def embed_one(self, text, task_type):
        self.embed_calls += 1
        return [1.0, 0.0]


def _service(gemini):
    from app.services.chat_service import ChatService

    service = ChatService(_FakeSession(), gemini=gemini)
    logged = []

    async def fake_list_for_chat(**kw):
        return [_FakeInsight("Tin A")]

    async def fake_create_log(**kw):
        logged.append(kw)

    service.insight_repo.list_for_chat = fake_list_for_chat
    service.chat_log_repo.create = fake_create_log
    return service, logged


@pytest.mark.asyncio
async def test_contentless_question_spends_no_embed_call():
    """"Có gì mới không?" — `_rank` sẽ bỏ tầng vector, nên gọi embed là tiêu ~1,4s chờ mạng
    cho một kết quả chắc chắn bị vứt. Phải bỏ HẲN lượt gọi, không phải gọi rồi bỏ kết quả."""
    gemini = _FakeGemini()
    service, _ = _service(gemini)

    await service.answer("Có gì mới không?", [], None)

    assert gemini.embed_calls == 0


@pytest.mark.asyncio
async def test_question_with_terms_does_spend_one_embed_call():
    gemini = _FakeGemini()
    service, _ = _service(gemini)

    await service.answer("kubernetes có lỗ hổng nào không", [], None)

    assert gemini.embed_calls == 1


@pytest.mark.asyncio
async def test_thinking_tokens_reach_the_chat_log():
    """Chi phí thinking phải đọc được THẲNG từ log, không phải suy ra từ hiệu ba con số."""
    gemini = _FakeGemini()
    service, logged = _service(gemini)

    await service.answer("kubernetes có lỗ hổng nào không", [], None)

    assert logged[0]["thinking_tokens"] == 111


@pytest.mark.asyncio
async def test_chat_log_accepts_unmeasured_thinking():
    """Nhà cung cấp im lặng ⇒ ghi NULL, lượt trả lời vẫn hoàn tất bình thường."""
    gemini = _FakeGemini()
    gemini.thinking = None
    service, logged = _service(gemini)

    result = await service.answer("kubernetes có lỗ hổng nào không", [], None)

    assert logged[0]["thinking_tokens"] is None
    assert result["answer"]
