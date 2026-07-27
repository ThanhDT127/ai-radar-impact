"""Embed lúc publish KHÔNG BAO GIỜ được chặn việc tạo insight (`chat-hybrid-retrieval`, D6).

Vì sao đáng một file riêng: lượt embed nằm ở CUỐI `analyze_document`, sau khi đã tốn hai
lượt gọi model (gate + deep analysis). Một lỗi ném ra ở đó vứt bỏ toàn bộ công đó và làm
mất luôn insight — đổi một suy giảm nhỏ (tin tạm thời chỉ xếp hạng được bằng lexical) lấy
một mất mát thật.

`embedding NULL` là trạng thái HỢP LỆ, `app.scripts.embed_insights` vá lại được về sau.
"""

import uuid
from types import SimpleNamespace

import pytest

from app.ai.gemini_client import AnalysisResult, GateResult
from app.services.analyzer import AnalyzerService


class _FakeRawDocRepo:
    def __init__(self):
        self.statuses: dict[uuid.UUID, str] = {}

    async def mark_gate_skipped(self, doc_id):
        pass

    async def update_status(self, doc_id, status):
        self.statuses[doc_id] = status


class _FakeInsightRepo:
    def __init__(self):
        self.created = []

    async def create(self, **kwargs):
        insight = SimpleNamespace(id=uuid.uuid4(), embedding=None, **kwargs)
        self.created.append(insight)
        return insight


class _FakeGemini:
    def __init__(self, embed_behaviour):
        self._embed = embed_behaviour
        self.embed_calls = 0

    def gate_analyze(self, title, content):
        return GateResult(pass_gate=True, actionability_score=0.7)

    def analyze(self, title, content):
        return AnalysisResult(
            topics=["AI/ML Ứng dụng"],
            event_type="Phát hành mới",
            nature="Cơ hội",
            summary_short="Tóm tắt tiếng Việt.",
            summary_medium="Tóm tắt dài hơn.",
            affected_roles=["Dev"],
            confidence=0.9,
            raw_response={},
            signal="Tín hiệu",
            so_what="Nên làm gì",
        )

    def embed_one(self, text, task_type):
        self.embed_calls += 1
        return self._embed(text)


def _doc():
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="Tin test",
        normalized_content="nội dung đủ dài " * 20,
        raw_content=None,
        published_at=None,
        source_id=uuid.uuid4(),
        source_url="https://example.com/a",
    )


def _source():
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="Nguồn test",
        trust_tier="high",
        region="global",
        config={},
    )


def _analyzer(embed_behaviour, monkeypatch):
    from app.services import analyzer as analyzer_mod

    monkeypatch.setattr(analyzer_mod.settings, "enable_gate", True)
    svc = AnalyzerService.__new__(AnalyzerService)
    svc.session = None
    svc.raw_doc_repo = _FakeRawDocRepo()
    svc.insight_repo = _FakeInsightRepo()
    svc.gemini = _FakeGemini(embed_behaviour)
    return svc


@pytest.mark.asyncio
async def test_embedding_stored_on_publish(monkeypatch):
    svc = _analyzer(lambda text: [0.1] * 768, monkeypatch)

    created = await svc.analyze_document(_doc(), _source())

    assert created is True
    assert svc.insight_repo.created[0].embedding == [0.1] * 768


@pytest.mark.asyncio
async def test_embed_returning_none_still_creates_insight(monkeypatch):
    """Vertex lỗi ⇒ `embed_one` trả None ⇒ insight vẫn ra đời với embedding NULL."""
    svc = _analyzer(lambda text: None, monkeypatch)
    doc = _doc()

    created = await svc.analyze_document(doc, _source())

    assert created is True
    assert svc.insight_repo.created[0].embedding is None
    assert svc.raw_doc_repo.statuses[doc.id] == "analyzed", "doc vẫn phải chốt là đã phân tích"


@pytest.mark.asyncio
async def test_embed_raising_still_creates_insight(monkeypatch):
    """Lỗi NÉM RA (client thiếu hàm, timeout, bug) cũng không được làm rơi insight.

    Ca này đã đỏ thật: bản đầu gọi thẳng `embed_one` không bọc try, và hai test trong
    `test_gate_skipped.py` gãy vì client giả ở đó không có hàm `embed_one`. Ngoài đời thì
    lỗi sẽ không lịch sự như vậy — nó tới sau khi đã tiêu hai lượt gọi model.
    """
    def boom(text):
        raise RuntimeError("Vertex embedding sự cố")

    svc = _analyzer(boom, monkeypatch)
    doc = _doc()

    created = await svc.analyze_document(doc, _source())

    assert created is True
    assert svc.insight_repo.created[0].embedding is None
    assert svc.raw_doc_repo.statuses[doc.id] == "analyzed"


@pytest.mark.asyncio
async def test_embedding_text_covers_the_documented_fields(monkeypatch):
    """`build_embedding_text` phải mang đúng bộ field của D2 — dùng chung với backfill."""
    seen = {}

    def capture(text):
        seen["text"] = text
        return [0.0] * 768

    svc = _analyzer(capture, monkeypatch)
    await svc.analyze_document(_doc(), _source())

    for expected in ("Tin test", "Tín hiệu", "Nên làm gì", "Tóm tắt tiếng Việt.", "AI/ML Ứng dụng"):
        assert expected in seen["text"], f"thiếu {expected!r} trong text embed"
