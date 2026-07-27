"""Xếp hạng lai vector + lexical (`chat-hybrid-retrieval`) — CƠ CHẾ, không phải chất lượng.

Ranh giới với `tests/eval/chat_rank_harness.py`: harness đo **chất lượng xếp hạng** (recall
trên 42 câu gán nhãn tay, corpus thật). File này khoá những bất biến **cấu trúc** mà harness
không nhìn thấy vì chúng chỉ lộ ra ở ca biên:

  - embed lỗi ⇒ chat vẫn trả lời, và trả lời theo ĐÚNG thứ tự lexical cũ (suy giảm êm);
  - `embedding IS NULL` ⇒ tin vẫn tham gia, không bị rơi khỏi tập ứng viên;
  - KHÔNG ngưỡng similarity ⇒ tập ứng viên không bao giờ rỗng vì "không đủ giống";
  - lượt embed KHÔNG tiêu budget `max_daily_chat_calls`.

Ca thật sau cùng — corpus tiếng Anh, câu hỏi tiếng Việt — dùng vector dựng tay chứ không
gọi Vertex: thứ đang đo là *phép trộn thứ hạng*, không phải chất lượng của model embedding.
"""

import uuid
from datetime import datetime

import pytest

from app.services.chat_service import (
    RRF_K,
    ChatService,
    _competition_ranks,
    _cosine,
)


class _FakeInsight:
    def __init__(self, title, text="", embedding=None, role_urgency="medium", impact="Trung bình"):
        self.id = uuid.uuid4()
        self.title = title
        self.signal = text or f"Ý nghĩa của {title}"
        self.so_what = ""
        self.summary_short = ""
        self.summary_medium = "vừa"
        self.affected_roles = ["Security"]
        self.topics = ["Security & Compliance"]
        self.source_url = f"https://example.com/{title}"
        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.impact_label = impact
        self.actionability_score = 0.5
        self.intelligence_tier = "Tactical"
        self.trust_score = 0.8
        self.practical_indicators = None
        self.embedding = embedding
        self.recommendations = {
            "Security": {"action_type": "read", "note": "n", "urgency": role_urgency}
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
    """Client giả: `chat` trả lời cố định, `embed_one` trả vector do test quyết."""

    def __init__(self, answer="Có tin này [1].", query_vector=None, embed_fails=False):
        self.answer = answer
        self.prompts = []
        self.query_vector = query_vector
        self.embed_fails = embed_fails
        self.embed_calls = 0

    def chat(self, system_prompt, user_prompt, state=None):
        self.prompts.append(user_prompt)
        return self.answer, 1

    def embed_one(self, text, task_type):
        self.embed_calls += 1
        if self.embed_fails:
            raise RuntimeError("Vertex embedding đang sự cố")
        return self.query_vector


def _service(candidates, gemini=None, quota_used=0):
    session = _FakeSession(quota_used)
    service = ChatService(session, gemini=gemini or _FakeGemini())

    async def fake_list_for_chat(**kw):
        return candidates

    logged = []

    async def fake_create_log(**kw):
        logged.append(kw)

    service.insight_repo.list_for_chat = fake_list_for_chat
    service.chat_log_repo.create = fake_create_log
    return service, logged


# --- Phép trộn thứ hạng -------------------------------------------------------------


def test_competition_ranks_gives_ties_the_same_rank():
    """Điểm bằng nhau ⇒ hạng bằng nhau. Phá hoà bằng thứ tự list = đưa nhiễu vào RRF."""
    assert _competition_ranks([5.0, 1.0, 5.0, 0.0]) == [1, 3, 1, 4]


def test_cosine_of_zero_vector_is_zero_not_nan():
    assert _cosine([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_rrf_constant_is_independent_of_top_k():
    """`RRF_K` trùng số 60 với `chat_index_top_k` chỉ là ngẫu nhiên — đừng gộp hai hằng số."""
    from app.config import settings

    settings.chat_index_top_k = 5
    try:
        assert RRF_K == 60
    finally:
        settings.chat_index_top_k = 60


# --- Suy giảm êm (design D6) --------------------------------------------------------


def test_no_query_vector_reproduces_lexical_order_exactly():
    """Đây là bất biến giữ cho fallback KHÔNG phải một đường xếp hạng thứ hai.

    RRF trên một tín hiệu là hàm đơn điệu của chính thứ hạng đó, nên thứ tự phải trùng khít
    bản lexical cũ. Nếu test này đỏ thì "suy giảm êm" đã lặng lẽ thành "xếp hạng khác đi".
    """
    items = [
        _FakeInsight("Tin về kubernetes", text="cụm kubernetes bị lỗi"),
        _FakeInsight("Tin về email", text="chiến dịch phishing qua email"),
        _FakeInsight("Tin về kubernetes nữa", text="bản vá kubernetes mới"),
    ]
    service, _ = _service(items)

    ranked = service._rank(items, "kubernetes có vấn đề gì", None)

    assert [i.title for i in ranked[:2]] == ["Tin về kubernetes", "Tin về kubernetes nữa"]


@pytest.mark.asyncio
async def test_embed_failure_still_answers(caplog):
    """Vertex embedding sự cố KHÔNG được biến thành lỗi cho người dùng (task 4.1)."""
    items = [_FakeInsight("Tin A", text="kubernetes")]
    gemini = _FakeGemini(embed_fails=True)
    service, _ = _service(items, gemini)

    result = await service.answer("kubernetes có gì mới", [], None)

    assert result["answer"] == "Có tin này [1]."
    assert result["mode"] == "global"
    assert gemini.prompts, "pipeline phải chạy tiếp tới lượt gọi model"


def test_insight_without_embedding_is_not_dropped():
    """`embedding IS NULL` ⇒ không có tầng vector, nhưng vẫn cạnh tranh đủ ở lexical (task 4.3)."""
    chưa_embed = _FakeInsight("Tin chưa embed", text="kubernetes bị lỗi", embedding=None)
    đã_embed = _FakeInsight("Tin lạc đề", text="thời tiết", embedding=[0.0, 1.0])
    service, _ = _service([chưa_embed, đã_embed])

    ranked = service._rank([chưa_embed, đã_embed], "kubernetes", [1.0, 0.0])

    assert len(ranked) == 2, "không tin nào được phép biến mất khỏi tập ứng viên"
    assert ranked[0] is chưa_embed, "khớp từ khoá thật phải thắng, dù chưa có vector"


def test_low_similarity_still_returns_candidates():
    """KHÔNG ngưỡng similarity: không tin nào 'đủ giống' vẫn phải trả về đủ danh sách."""
    items = [_FakeInsight("A", embedding=[1.0, 0.0]), _FakeInsight("B", embedding=[0.9, 0.1])]
    service, _ = _service(items)

    ranked = service._rank(items, "câu hỏi hoàn toàn khác chủ đề", [0.0, -1.0])

    assert len(ranked) == 2


# --- Tầng vector thật sự đổi được thứ hạng ------------------------------------------


def test_semantic_match_outranks_keyword_noise():
    """Ca `sa thải ↔ layoff`: tin đúng KHÔNG trùng từ khoá nào vẫn phải lên trên (task 4.2).

    Vector dựng tay: tin `layoff` nằm cùng hướng với câu hỏi, tin còn lại vuông góc.
    """
    layoff = _FakeInsight("Big Tech layoffs hit AI teams", text="downsizing", embedding=[1.0, 0.0])
    noise = _FakeInsight("Tin lạc đề", text="cách nướng bánh", embedding=[0.0, 1.0])
    service, _ = _service([noise, layoff])

    lexical = service._rank([noise, layoff], "các tập đoàn cắt giảm nhân sự", None)
    hybrid = service._rank([noise, layoff], "các tập đoàn cắt giảm nhân sự", [1.0, 0.0])

    assert lexical[0] is noise, "tiền đề: lexical thuần không phân biệt được (hoà, rơi về importance)"
    assert hybrid[0] is layoff, "tầng vector phải kéo tin đúng ngữ nghĩa lên đầu"


def test_contentless_question_ignores_vector_layer():
    """"Có gì mới không?" — mọi từ là stopword ⇒ embedding là nhiễu, phải nhường độ quan trọng.

    Đo 27/07/2026: bỏ cổng này thì `rank-generic` tụt recall@5 từ 1,00 xuống 0,00 vì tin
    CISA khẩn cấp rơi xuống hạng 23 nhường chỗ cho tin có vector tình cờ gần câu hỏi rỗng.
    """
    khẩn = _FakeInsight("Tin khẩn", role_urgency="high", embedding=[0.0, 1.0])
    thường = _FakeInsight("Tin thường", role_urgency="low", embedding=[1.0, 0.0])
    service, _ = _service([thường, khẩn])

    ranked = service._rank([thường, khẩn], "Có gì mới không?", [1.0, 0.0])

    assert ranked[0] is khẩn


# --- Đơn vị budget ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embedding_does_not_consume_chat_call_budget():
    """Lượt embed rẻ hơn lượt sinh văn bản vài bậc — trộn chung là để nó bào mòn budget đắt."""
    items = [_FakeInsight("Tin A", text="kubernetes", embedding=[1.0, 0.0])]
    gemini = _FakeGemini(query_vector=[1.0, 0.0])
    service, logged = _service(items, gemini)

    await service.answer("kubernetes có gì mới", [], None)

    assert gemini.embed_calls == 1, "câu hỏi phải được embed đúng một lần"
    assert logged[0]["model_calls"] == 1, "chỉ lượt `chat()` mới tính vào budget"
