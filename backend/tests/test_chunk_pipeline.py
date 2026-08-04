"""Tín hiệu xếp hạng mức ĐOẠN — vòng đời, suy giảm êm, và ranh giới với trích dẫn.

Bốn bất biến, mỗi cái tương ứng một chế độ hỏng đã lường trước:

  ① sinh đoạn lỗi **không** chặn tạo insight (như `_attach_embedding` của D6)
  ② tin CHƯA có đoạn không bị phạt ngầm — nếu không, cửa sổ backfill thành thiên lệch hệ thống
  ③ truy vấn đoạn lỗi ⇒ thứ tự **trùng khít** bản hai tín hiệu (suy giảm êm là bất biến)
  ④ đoạn KHÔNG BAO GIỜ là đích của marker `[n]`

Không file nào ở đây chạm DB hay model.
"""

import uuid
from types import SimpleNamespace

import pytest

from app.ai.gemini_client import AnalysisResult, GateResult
from app.services.analyzer import AnalyzerService
from app.services.chat_service import ChatService


# --- Fakes dùng chung -----------------------------------------------------------------


class _FakeChunkRepo:
    def __init__(self, fail: bool = False):
        self.calls: list[dict] = []
        self.deleted: list[list[uuid.UUID]] = []
        self._fail = fail

    async def replace_for_document(self, raw_document_id, insight_id, chunks, embeddings):
        if self._fail:
            raise RuntimeError("DB từ chối ghi đoạn")
        self.calls.append(
            {
                "raw_document_id": raw_document_id,
                "insight_id": insight_id,
                "chunks": chunks,
                "embeddings": embeddings,
            }
        )
        return len(chunks)

    async def delete_for_documents(self, raw_document_ids):
        self.deleted.append(list(raw_document_ids))
        return len(raw_document_ids)


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
    """Client giả: `embed` (lô, cho đoạn) và `embed_one` (cho insight)."""

    def __init__(self, embed_batch=None):
        self._embed_batch = embed_batch or (lambda texts: [[0.2] * 768 for _ in texts])

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
        return [0.1] * 768

    def embed(self, texts, task_type):
        return self._embed_batch(texts)


_DEFAULT_BODY = "Nội dung thân bài. " * 200


def _doc(content: str | None = _DEFAULT_BODY):
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="Tin test",
        normalized_content=content,
        raw_content=None,
        published_at=None,
        source_id=uuid.uuid4(),
        source_url="https://example.com/a",
    )


def _source():
    return SimpleNamespace(
        id=uuid.uuid4(), name="Nguồn test", trust_tier="high", region="global", config={}
    )


def _analyzer(monkeypatch, chunk_repo=None, gemini=None):
    from app.services import analyzer as analyzer_mod

    monkeypatch.setattr(analyzer_mod.settings, "enable_gate", True)
    svc = AnalyzerService.__new__(AnalyzerService)
    svc.session = None
    svc.raw_doc_repo = _FakeRawDocRepo()
    svc.insight_repo = _FakeInsightRepo()
    svc.chunk_repo = chunk_repo or _FakeChunkRepo()
    svc.gemini = gemini or _FakeGemini()
    return svc


# --- ① Vòng đời: lỗi sinh đoạn không chặn tạo insight ----------------------------------


@pytest.mark.asyncio
async def test_chunks_written_on_publish(monkeypatch):
    chunk_repo = _FakeChunkRepo()
    svc = _analyzer(monkeypatch, chunk_repo)
    doc = _doc()

    assert await svc.analyze_document(doc, _source()) is True

    assert len(chunk_repo.calls) == 1
    call = chunk_repo.calls[0]
    assert call["raw_document_id"] == doc.id
    assert call["insight_id"] == svc.insight_repo.created[0].id, "đoạn phải nối vào insight"
    assert len(call["chunks"]) == len(call["embeddings"]) > 0


@pytest.mark.asyncio
async def test_chunk_embed_failure_still_creates_insight(monkeypatch):
    """Vertex trả None cho cả lô ⇒ insight vẫn ra đời, đoạn lưu với embedding NULL."""
    chunk_repo = _FakeChunkRepo()
    gemini = _FakeGemini(embed_batch=lambda texts: [None for _ in texts])
    svc = _analyzer(monkeypatch, chunk_repo, gemini)
    doc = _doc()

    assert await svc.analyze_document(doc, _source()) is True
    assert svc.raw_doc_repo.statuses[doc.id] == "analyzed"
    assert all(v is None for v in chunk_repo.calls[0]["embeddings"])


@pytest.mark.asyncio
async def test_chunk_write_raising_still_creates_insight(monkeypatch):
    """Lỗi NÉM RA ở tầng ghi đoạn tới SAU khi đã tốn hai lượt gọi model + đã tạo insight.

    Vứt bỏ ngần ấy công vì một tín hiệu xếp hạng phụ trợ là cái giá không tương xứng.
    """
    chunk_repo = _FakeChunkRepo(fail=True)
    svc = _analyzer(monkeypatch, chunk_repo)
    doc = _doc()

    assert await svc.analyze_document(doc, _source()) is True
    assert svc.insight_repo.created, "insight vẫn phải tồn tại"
    assert svc.raw_doc_repo.statuses[doc.id] == "analyzed"


@pytest.mark.asyncio
async def test_body_too_short_to_chunk_makes_no_chunks(monkeypatch):
    """Thân bài ngắn hơn `MIN_CHARS` (mẩu RSS chỉ có một dòng) — không đoạn, không lỗi.

    Bài KHÔNG có content thì `analyze_document` bỏ qua từ đầu, nên ca đáng test là bài có
    content nhưng quá ngắn để cắt: một đoạn 30 ký tự chỉ thêm một vector nhiễu vào bảng.
    """
    chunk_repo = _FakeChunkRepo()
    svc = _analyzer(monkeypatch, chunk_repo)

    assert await svc.analyze_document(_doc(content="Tin ngắn một dòng."), _source()) is True
    assert svc.insight_repo.created, "insight vẫn phải ra đời"
    assert chunk_repo.calls == []


# --- ② + ③ Xếp hạng ------------------------------------------------------------------


def _insight(title: str, embedding=None, **kw):
    from app.models.insight import Insight

    insight = Insight(
        id=uuid.uuid4(),
        title=title,
        source_url="https://example.com",
        topics=kw.get("topics", []),
        affected_roles=kw.get("affected_roles", ["Dev"]),
        impact_label=kw.get("impact_label", "Trung bình"),
        trust_score=0.8,
        actionability_score=0.5,
    )
    insight.embedding = embedding
    return insight


def _service():
    return ChatService.__new__(ChatService)


def test_insight_without_chunks_is_not_penalized():
    """Tin khớp CHÍNH XÁC từ khoá nhưng chưa được chunk phải thắng tin lạc đề đã chunk.

    Đây là bản sao của `test_insight_without_embedding_is_not_dropped` cho tầng thứ ba, và
    nó bắt đúng một cách viết sai rất tự nhiên: bỏ số hạng thứ ba cho tin thiếu đoạn. Làm
    vậy là phạt ngầm một phần ba số điểm, nên trong cửa sổ backfill (gần như mọi tin đều
    thiếu đoạn) nó thành một thiên lệch hệ thống — im lặng.
    """
    matching = _insight("Kubernetes 1.35 vá lỗ hổng nghiêm trọng")   # chưa chunk
    off_topic = _insight("Bản tin thị trường quảng cáo tuần này")     # đã chunk, lạc đề

    ranked = _service()._rank(
        [off_topic, matching],
        "kubernetes có lỗ hổng gì",
        query_vector=None,
        chunk_ranks={off_topic.id: 1},
    )

    assert ranked[0] is matching


def test_chunk_signal_lifts_an_insight_whose_analysis_never_mentions_the_term():
    """Chính chế độ hỏng mà change này sinh ra để chữa."""
    hidden = _insight("Camera thông minh rò rỉ dữ liệu vị trí")   # thân bài có "SquashFS"
    other = _insight("Tổng hợp tin công nghệ trong tuần")

    # Cả hai bài đều đã được chunk; chỉ một bài có đoạn thật sự nhắc `squashfs`. Đây là
    # hình dạng THẬT của dữ liệu — không phải "một bên có đoạn, một bên không" (ca đó là
    # test mượn-hạng ở trên, và ở đó hoà nhau mới là đúng).
    chunk_ranks = {hidden.id: 1, other.id: 240}

    without = _service()._rank([other, hidden], "bài nào dùng squashfs", None, None)
    with_chunks = _service()._rank([other, hidden], "bài nào dùng squashfs", None, chunk_ranks)

    assert without[0] is other, "không có tín hiệu đoạn thì không gì phân biệt được hai tin"
    assert with_chunks[0] is hidden


def test_missing_chunk_signal_keeps_the_two_signal_order_exactly():
    """③ Suy giảm êm là **trùng khít**, không phải "gần giống".

    Ca này bắt một cách viết sai tinh vi: cho `rank_chunk = rank_vector` khi cả lượt không
    có tín hiệu đoạn. Nó *có vẻ* nhất quán với luật mượn hạng của D2, nhưng thực ra nhân
    đôi trọng số tầng vector và sinh ra một thứ tự thứ ba — xuất hiện đúng vào lúc hệ thống
    đang hỏng, tức là lúc khó phát hiện nhất.
    """
    corpus = [
        _insight("Kubernetes vá lỗi", embedding=[1.0] + [0.0] * 767),
        _insight("Kubernetes ra bản mới", embedding=[0.9, 0.1] + [0.0] * 766),
        _insight("Tin thị trường", embedding=[0.0, 1.0] + [0.0] * 766),
        _insight("Ghi chú vận hành kubernetes"),
    ]
    question = "kubernetes có gì mới"
    query_vector = [1.0] + [0.0] * 767

    baseline = _service()._rank(list(corpus), question, query_vector)
    for empty in (None, {}):
        degraded = _service()._rank(list(corpus), question, query_vector, empty)
        assert [i.id for i in degraded] == [i.id for i in baseline]


def test_chunk_ranks_are_ignored_when_question_has_no_keywords():
    """Câu rỗng từ khoá ("Có gì mới không?") tắt tầng vector — tầng đoạn đi theo.

    Cùng lý do đã đo ở `chat-hybrid-retrieval`: câu không có chủ đề thì mọi thứ "hơi giống",
    và cái hơi giống đó **đè** tầng độ quan trọng bằng nhiễu.
    """
    important = _insight("CISA yêu cầu vá khẩn", impact_label="Nghiêm trọng")
    noise = _insight("Ghi chú linh tinh", impact_label="Theo dõi")

    # ⚠️ Hai thứ hạng phải LỆCH HẲN nhau. Bản đầu của test này truyền `{noise.id: 1}` và để
    # tin kia mượn hạng — hai bên cùng ra 1, hoà, rồi `importance` quyết ⇒ test XANH kể cả
    # khi cổng không tồn tại. Nó chỉ bắt được lỗi khi tín hiệu đoạn thực sự có sức nặng.
    chunk_ranks = {noise.id: 1, important.id: 200}

    ranked = _service()._rank(
        [noise, important], "Có gì mới không?", [1.0] + [0.0] * 767, chunk_ranks
    )

    assert ranked[0] is important, (
        "câu rỗng từ khoá phải rơi về độ quan trọng — đây là ca `rank-generic` đã đo được: "
        "bỏ cổng này thì tin CISA vá khẩn rơi xuống hạng 109/179"
    )


@pytest.mark.asyncio
async def test_chunk_query_raising_degrades_to_two_signals():
    """③ ở mức SERVICE: truy vấn đoạn ném lỗi ⇒ `{}` ⇒ chat vẫn trả lời, không 500.

    Test `_rank` ở trên khoá phần *công thức*; cái này khoá phần *đường ống*. Hai chỗ khác
    nhau: `_rank` không bao giờ thấy exception, nó chỉ thấy `{}` — nên nếu `_chunk_ranks`
    quên bọc try thì mọi câu hỏi toàn cục thành HTTP 500 mà không test nào ở trên đỏ.
    """
    from app.config import settings

    service = ChatService.__new__(ChatService)

    class _BoomRepo:
        async def retrieve_chunk_ranks(self, _vector):
            raise RuntimeError("pgvector sự cố")

    service.chunk_repo = _BoomRepo()
    monkey = settings.chat_embedding_enabled
    try:
        assert await service._chunk_ranks([0.1] * 768) == {}
    finally:
        settings.chat_embedding_enabled = monkey


@pytest.mark.asyncio
async def test_chunk_ranks_skipped_when_embedding_disabled():
    """`chat_embedding_enabled=false` ⇒ không truy vấn DB lần nào (repo nổ nếu bị chạm)."""
    from app.config import settings

    service = ChatService.__new__(ChatService)

    class _NeverRepo:
        async def retrieve_chunk_ranks(self, _vector):
            raise AssertionError("không được truy vấn khi embedding đã tắt")

    service.chunk_repo = _NeverRepo()
    original = settings.chat_embedding_enabled
    settings.chat_embedding_enabled = False
    try:
        assert await service._chunk_ranks([0.1] * 768) == {}
    finally:
        settings.chat_embedding_enabled = original


# --- ② Vòng đời: purge xoá đoạn cùng lúc với thân bài ----------------------------------


@pytest.mark.asyncio
async def test_purge_deletes_chunks_of_expiring_documents(monkeypatch):
    """`ON DELETE CASCADE` KHÔNG đủ: purge không xoá hàng, nó chỉ rỗng hoá content.

    Quên bước xoá tường minh thì corpus vector giữ nguyên nội dung mà chính sách lưu trữ
    vừa yêu cầu xoá — và giữ ở dạng đọc lại được (`document_chunks.content`).
    """
    from app.scripts import purge_expired as purge_mod

    expiring = [uuid.uuid4(), uuid.uuid4()]
    order: list[str] = []
    chunk_repo = _FakeChunkRepo()

    class _RawRepo:
        def __init__(self, session):
            pass

        async def ids_older_than(self, cutoff):
            order.append("ids")
            return expiring

        async def tombstone_older_than(self, cutoff):
            order.append("tombstone")
            return len(expiring)

    class _InsightRepo:
        def __init__(self, session):
            pass

        async def expire_older_than(self, cutoff):
            return 1

    class _Session:
        async def commit(self):
            pass

    monkeypatch.setattr(purge_mod, "RawDocumentRepository", _RawRepo)
    monkeypatch.setattr(purge_mod, "InsightRepository", _InsightRepo)
    monkeypatch.setattr(purge_mod, "DocumentChunkRepository", lambda session: chunk_repo)

    counts = await purge_mod.purge_expired(_Session())

    assert chunk_repo.deleted == [expiring]
    assert counts["chunks_deleted"] == 2
    # Hỏi id TRƯỚC khi tombstone: sau lượt update thì vị từ đó trả rỗng và đoạn sống sót.
    assert order == ["ids", "tombstone"]
