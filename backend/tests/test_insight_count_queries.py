"""Hồi quy cho fix-insight-count-is-primary.

Các bộ đếm insight hướng người dùng phải đếm theo đại diện cụm dedup (`is_primary`),
khớp với `list_paginated`. Trước fix, KPI hiện 71 nhưng chỉ xem được 64; chip nguồn
`LinkedIn - OpenAI` hiện 5 nhưng bấm vào chỉ có 2.

Test soi SQL compile được thay vì chạy trên DB thật — suite hiện không có hạ tầng
test DB, và điều cần khóa lại là *hình dạng query*, đặc biệt việc `is_primary` của
`list_with_insight_counts` phải nằm trong `JOIN ... ON` chứ không phải `WHERE`
(xem design.md D2: đưa vào WHERE sẽ làm biến mất mọi nguồn không có insight primary).
"""

import pytest
from sqlalchemy.dialects import postgresql

from app.repositories.insight_repo import InsightRepository
from app.repositories.source_repo import SourceRepository


def _sql(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


class _FakeResult:
    """Kết quả giả đủ dùng cho cả hai repo (one/scalar_one/iter)."""

    class _Row:
        total = critical_high = opportunities = 0
        _mapping: dict = {}

    def one(self):
        return self._Row()

    def scalar_one(self):
        return 0

    def __iter__(self):
        return iter(())


class _RecordingSession:
    """Ghi lại mọi statement được execute để soi SQL."""

    def __init__(self):
        self.statements = []

    async def execute(self, statement, *a, **kw):
        self.statements.append(statement)
        return _FakeResult()


@pytest.mark.asyncio
async def test_get_stats_counts_only_primary():
    """KPI không được đếm bản trùng — nếu không, số KPI > số thẻ xem được."""
    session = _RecordingSession()
    await InsightRepository(session).get_stats()

    # statement đầu là truy vấn 3 aggregate; statement sau là đếm source active.
    sql = _sql(session.statements[0])
    assert "is_primary" in sql, "get_stats đang đếm cả insight non-primary"
    assert "WHERE" in sql and "is_primary" in sql.split("WHERE", 1)[1], (
        "is_primary phải nằm trong WHERE của get_stats"
    )


@pytest.mark.asyncio
async def test_source_counts_only_primary():
    """Chip nguồn phải đếm theo cụm, khớp với số thẻ khi lọc theo nguồn đó."""
    session = _RecordingSession()
    await SourceRepository(session).list_with_insight_counts()

    sql = _sql(session.statements[0])
    assert "is_primary" in sql, "list_with_insight_counts đang đếm cả insight non-primary"


@pytest.mark.asyncio
async def test_source_counts_keep_sources_without_primary_insights():
    """D2: `is_primary` phải ở JOIN ... ON, KHÔNG ở WHERE.

    Ở WHERE thì nguồn không có insight primary sẽ bị loại khỏi kết quả, làm hỏng
    nhóm "chưa có insight" trên UI. Ở ON thì hàng vẫn còn, count về 0.
    """
    session = _RecordingSession()
    await SourceRepository(session).list_with_insight_counts()

    sql = _sql(session.statements[0])
    join_part, _, after_join = sql.partition("GROUP BY")

    assert "is_primary" in join_part, "is_primary phải nằm trong mệnh đề JOIN ... ON"
    assert "WHERE" not in sql, (
        "query không được có WHERE — thêm điều kiện vào WHERE sẽ loại bỏ "
        "các nguồn chưa có insight primary khỏi kết quả"
    )


class _ScalarResult(_FakeResult):
    """`list_for_chat` dùng `.scalars().unique().all()` thay vì one/scalar_one."""

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return []


class _ScalarRecordingSession(_RecordingSession):
    async def execute(self, statement, *a, **kw):
        self.statements.append(statement)
        return _ScalarResult()


@pytest.mark.asyncio
async def test_list_for_chat_filters_primary_and_published():
    """Index của chatbot phải khớp tập tin dashboard hiển thị.

    Thiếu `is_primary` thì chat trích dẫn bản trùng của cụm dedup — người dùng bấm
    citation sẽ tới một tin không có trong danh sách.
    """
    session = _ScalarRecordingSession()
    await InsightRepository(session).list_for_chat()

    sql = _sql(session.statements[0])
    where_part = sql.split("WHERE", 1)[1]
    assert "is_primary" in where_part, "list_for_chat đang lấy cả insight non-primary"
    assert "status" in where_part, "list_for_chat phải lọc status = published"
