"""`gate_skipped` phải phân biệt "qua gate thật" với "bỏ qua gate do lỗi" (fail-open).

Không có cột này thì doc fail-open trông y hệt doc qua gate, làm tỉ lệ qua gate
bị thổi lên (đo 20/07/2026: thô 18/24/26/36% so với thật 13/17/20/22%).

Test chạy thẳng `AnalyzerService.analyze_document` với Gemini giả, không chép lại
logic nhánh vào test.
"""

import uuid
from types import SimpleNamespace

import pytest

from app.ai.gemini_client import AnalysisResult, GateResult
from app.services.analyzer import AnalyzerService


class FakeRawDocRepo:
    def __init__(self):
        self.gate_skipped_ids: list[uuid.UUID] = []
        self.statuses: dict[uuid.UUID, str] = {}

    async def mark_gate_skipped(self, doc_id):
        self.gate_skipped_ids.append(doc_id)

    async def update_status(self, doc_id, status):
        self.statuses[doc_id] = status


class FakeInsightRepo:
    def __init__(self):
        self.created = []

    async def create(self, **kwargs):
        insight = SimpleNamespace(id=uuid.uuid4(), **kwargs)
        self.created.append(insight)
        return insight


class FakeGemini:
    """Gate trả `gate_result`; deep analysis luôn trả một kết quả hợp lệ."""

    def __init__(self, gate_result):
        self._gate_result = gate_result
        self.analyze_calls = 0

    def gate_analyze(self, title, content):
        return self._gate_result

    def analyze(self, title, content):
        self.analyze_calls += 1
        return AnalysisResult(
            topics=["AI/ML Ứng dụng"],
            event_type="Phát hành mới",
            nature="Cơ hội",
            summary_short="Tóm tắt tiếng Việt.",
            summary_medium="Tóm tắt dài hơn.",
            affected_roles=["Dev"],
            confidence=0.9,
            raw_response={},
        )


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


def _analyzer(gate_result, monkeypatch):
    from app.services import analyzer as analyzer_mod

    monkeypatch.setattr(analyzer_mod.settings, "enable_gate", True)
    svc = AnalyzerService.__new__(AnalyzerService)
    svc.session = None
    svc.raw_doc_repo = FakeRawDocRepo()
    svc.insight_repo = FakeInsightRepo()
    svc.gemini = FakeGemini(gate_result)
    return svc


@pytest.mark.asyncio
async def test_gate_error_marks_gate_skipped(monkeypatch):
    """Gate lỗi parse ⇒ fail-open: vẫn deep analysis NHƯNG đánh dấu gate_skipped."""
    svc = _analyzer(
        GateResult(pass_gate=True, error="Expecting ',' delimiter"), monkeypatch
    )
    doc = _doc()

    await svc.analyze_document(doc, _source())

    assert svc.raw_doc_repo.gate_skipped_ids == [doc.id]
    assert svc.gemini.analyze_calls == 1, "fail-open vẫn phải chạy deep analysis"


@pytest.mark.asyncio
async def test_gate_pass_does_not_mark_gate_skipped(monkeypatch):
    """Gate chấm và cho qua ⇒ gate_skipped giữ nguyên False."""
    svc = _analyzer(
        GateResult(pass_gate=True, actionability_score=0.7, error=None), monkeypatch
    )

    await svc.analyze_document(_doc(), _source())

    assert svc.raw_doc_repo.gate_skipped_ids == []
    assert svc.gemini.analyze_calls == 1


@pytest.mark.asyncio
async def test_gate_filtered_marks_low_signal_without_deep_analysis(monkeypatch):
    """Gate loại tin ⇒ low_signal, không tốn deep analysis, không đánh dấu skipped."""
    svc = _analyzer(
        GateResult(pass_gate=False, actionability_score=0.1, gate_reason="nhiễu"),
        monkeypatch,
    )
    doc = _doc()

    await svc.analyze_document(doc, _source())

    assert svc.raw_doc_repo.statuses[doc.id] == "low_signal"
    assert svc.raw_doc_repo.gate_skipped_ids == []
    assert svc.gemini.analyze_calls == 0


def test_raw_document_defaults_gate_skipped_false():
    from app.models.raw_document import RawDocument

    col = RawDocument.__table__.c.gate_skipped
    assert col.nullable is False
    assert col.default.arg is False
