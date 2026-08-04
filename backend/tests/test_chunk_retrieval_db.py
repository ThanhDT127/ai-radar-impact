"""`retrieve_chunk_ranks` — phần CHẠM DB của tầng đoạn (design D4, cột "mất" của phương án B).

Bộ đo xếp hạng (RS harness) cố ý **không** phủ hàm này: nó đo `_rank`, và `_rank` phải thuần
để chạy miễn phí trong `pytest` mặc định. Nên phần SQL cần một lưới riêng — chính là file này.

**Cần DB**, nên nó tự skip khi không có. Đừng "sửa" bằng cách mock `session.execute`: thứ
đáng sai ở đây là `ORDER BY embedding <=>`, phép gộp `min` về insight, và bộ lọc
`embedding IS NOT NULL` — mock hết chúng đi thì test chỉ còn khẳng định Python gọi Python.

    docker compose exec backend python -m pytest tests/test_chunk_retrieval_db.py -q
"""

import uuid

import pytest

from app.database import async_session_maker
from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repo import DocumentChunkRepository

pytestmark = pytest.mark.asyncio

DIM = 768


def _vec(*head: float) -> list[float]:
    """Vector đơn vị thưa: chỉ vài chiều đầu khác 0, phần còn lại 0."""
    return list(head) + [0.0] * (DIM - len(head))


async def _session_or_skip():
    """Session mới, gắn vào event loop CỦA TEST NÀY.

    ⚠️ `engine.dispose()` là bắt buộc, không phải dọn dẹp cho gọn: `async_session_maker`
    dùng một engine module-level, mà pytest-asyncio cấp cho mỗi test một event loop mới.
    Kết nối còn trong pool thuộc loop của test trước ⇒ *"attached to a different loop"*.
    Bản đầu của file này bắt luôn lỗi đó rồi `skip`, nên ba test "xanh" thực ra là một test
    chạy và hai test bị bỏ qua **trong im lặng** — đúng kiểu hỏng mà một bộ đo không được có.

    Chỉ skip khi thật sự không nối được DB; mọi lỗi khác phải nổ.
    """
    from sqlalchemy.exc import InterfaceError, OperationalError

    from app.database import engine

    await engine.dispose()
    session = async_session_maker()
    try:
        await session.connection()
    except (OperationalError, InterfaceError, OSError) as e:  # pragma: no cover — DB tắt
        await session.close()
        pytest.skip(f"cần DB đang chạy: {e}")
    return session


async def _seed(session, chunks_per_insight: list[list[list[float] | None]]):
    """Dựng 1 nguồn + 1 bài gốc + N insight, mỗi insight kèm danh sách vector đoạn.

    Dùng ORM chứ không SQL thô: tên cột là thứ đổi được, và một test hỏng vì gõ sai tên cột
    không nói lên điều gì về hàm đang đo. Mọi thứ rollback ở cuối test.
    """
    from app.models.insight import Insight
    from app.models.raw_document import RawDocument
    from app.models.source import Source

    source = Source(name="test", source_type="rss", trust_tier="high", config={})
    session.add(source)
    await session.flush()

    doc = RawDocument(
        source_id=source.id,
        source_url="https://x.test/a",
        fingerprint=uuid.uuid4().hex,
        processing_status="analyzed",
    )
    session.add(doc)
    await session.flush()

    insight_ids = []
    ordinal = 0
    for n, vectors in enumerate(chunks_per_insight):
        insight = Insight(
            raw_document_id=doc.id,
            title=f"Tin {n}",
            source_url="https://x.test/a",
            topics=[],
            affected_roles=[],
        )
        session.add(insight)
        await session.flush()
        insight_ids.append(insight.id)
        for embedding in vectors:
            session.add(
                DocumentChunk(
                    raw_document_id=doc.id,
                    insight_id=insight.id,
                    ordinal=ordinal,
                    content=f"đoạn {ordinal}",
                    embedding=embedding,
                )
            )
            ordinal += 1
    await session.flush()
    return doc.id, insight_ids


async def test_returns_best_rank_per_insight():
    """D1: insight nhận thứ hạng của đoạn KHỚP TỐT NHẤT, không phải trung bình.

    Bài A dài, có MỘT đoạn trùng khít câu hỏi và hai đoạn lạc đề. Bài B ngắn, một đoạn khớp
    vừa phải. Gộp bằng trung bình thì A thua B chỉ vì A dài — đúng thiên lệch ngầm mà D1
    loại bỏ, và cũng là lý do `_vector_ranks` không cho tin thiếu embedding điểm 0.
    """
    session = await _session_or_skip()
    async with session:
        _, (a, b) = await _seed(
            session,
            [
                [_vec(1.0), _vec(0.0, 0.0, 1.0), _vec(0.0, 0.0, 0.0, 1.0)],  # A: 1 khớp + 2 lạc
                [_vec(0.7, 0.7)],                                            # B: khớp vừa phải
            ],
        )
        repo = DocumentChunkRepository(session)

        ranks = await repo.retrieve_chunk_ranks(_vec(1.0))

        # ⚠️ Truy vấn chạy trên DB THẬT nên `ranks` còn chứa corpus đã backfill — chỉ khẳng
        # định về hai tin vừa seed. Đây không phải hạn chế của test mà là bản chất của việc
        # đo một truy vấn: nó thấy mọi thứ trong bảng, y như production.
        assert ranks[a] == 1, "đoạn khớp nhất của A phải cho A hạng 1 (vector trùng khít)"
        assert ranks[b] > ranks[a], "B khớp kém hơn thì phải xếp sau"
        # Ba đoạn của A gộp thành ĐÚNG một mục — nếu gộp sai, A sẽ chiếm nhiều suất trong
        # `limit` và đẩy tin khác ra khỏi tín hiệu.
        assert sum(1 for k in ranks if k == a) == 1
        await session.rollback()


async def test_null_embedding_and_unlinked_chunks_are_excluded():
    session = await _session_or_skip()
    async with session:
        doc_id, (only,) = await _seed(session, [[None]])
        # Đoạn chưa nối được vào insight (ingest chạy trước analyze) — không có tin để gán
        # thứ hạng cho, nên phải bị loại ngay ở SQL, không chiếm suất trong `limit`.
        session.add(
            DocumentChunk(
                raw_document_id=doc_id, insight_id=None, ordinal=99,
                content="đoạn mồ côi", embedding=_vec(1.0),
            )
        )
        await session.flush()
        repo = DocumentChunkRepository(session)

        ranks = await repo.retrieve_chunk_ranks(_vec(1.0), limit=1000)

        # Đoạn duy nhất của `only` có `embedding IS NULL` ⇒ tin đó không có tín hiệu đoạn,
        # dù vector câu hỏi trùng khít đoạn mồ côi cùng bài.
        assert only not in ranks
        # Đoạn mồ côi (`insight_id IS NULL`) không thể thành khoá — nó không có tin để gán
        # thứ hạng cho, và để lọt vào thì nó chiếm suất trong `limit` của tin khác.
        assert None not in ranks
        await session.rollback()


async def test_none_query_vector_short_circuits():
    """Không có vector câu hỏi ⇒ `{}` và KHÔNG chạm DB (suy giảm êm, không tốn truy vấn)."""
    repo = DocumentChunkRepository(session=None)
    assert await repo.retrieve_chunk_ranks(None) == {}


async def test_ranks_real_corpus_and_maps_to_insights():
    """Trên corpus THẬT đã backfill: thứ hạng phải liên tục từ 1 và trỏ insight có thật."""
    session = await _session_or_skip()
    async with session:
        repo = DocumentChunkRepository(session)
        if await repo.count() == 0:
            pytest.skip("chưa backfill: chạy `python -m app.scripts.chunk_documents`")

        ranks = await repo.retrieve_chunk_ranks(_vec(1.0), limit=50)

        assert ranks, "corpus có đoạn thì phải có thứ hạng"
        assert min(ranks.values()) == 1, "thứ hạng bắt đầu từ 1"
        assert len(set(ranks.values())) == len(ranks), "mỗi insight đúng một thứ hạng"
        assert max(ranks.values()) <= 50, "không vượt quá limit"
