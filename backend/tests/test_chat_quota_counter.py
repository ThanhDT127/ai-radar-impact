"""Counter budget chat: ranh giới ngày phải theo UTC, khớp analysis.

`RawDocumentRepository.count_analyzed_today()` cắt ngày theo UTC. Nếu chat cắt theo giờ
VN thì hai budget reset lệch nhau 7 tiếng, và khoảng 17:00–24:00 giờ VN sẽ có hai "ngày"
chồng lên nhau — rất khó truy khi budget cạn sớm hơn dự kiến.

Suite không có hạ tầng DB test (xem `test_insight_count_queries.py`), nên test soi hàm
tính mốc + hình dạng SQL.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.dialects import postgresql

from app.repositories.chat_log_repo import ChatLogRepository, utc_day_bounds


def _sql(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


class _FakeResult:
    def scalar_one(self):
        return 0


class _RecordingSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement, *a, **kw):
        self.statements.append(statement)
        return _FakeResult()


def test_day_bounds_are_utc_midnight():
    start, end = utc_day_bounds(datetime(2026, 7, 22, 13, 45, 0, tzinfo=timezone.utc))
    assert start == datetime(2026, 7, 22, 0, 0, 0)
    assert end == datetime(2026, 7, 23, 0, 0, 0)


def test_day_bounds_cut_at_utc_not_vietnam_time():
    """23:30 giờ VN ngày 22/07 = 16:30 UTC cùng ngày → vẫn là ngày 22 theo UTC.

    Nếu cắt theo giờ VN thì mốc này đã sang ngày mới và budget reset sớm 7 tiếng.
    """
    vn_late_evening = datetime(2026, 7, 22, 16, 30, 0, tzinfo=timezone.utc)
    start, _ = utc_day_bounds(vn_late_evening)
    assert start == datetime(2026, 7, 22, 0, 0, 0)


def test_day_bounds_just_before_and_after_utc_midnight():
    before = datetime(2026, 7, 22, 23, 59, 59, tzinfo=timezone.utc)
    after = before + timedelta(seconds=1)

    assert utc_day_bounds(before)[0] == datetime(2026, 7, 22, 0, 0, 0)
    assert utc_day_bounds(after)[0] == datetime(2026, 7, 23, 0, 0, 0)


def test_day_bounds_normalize_non_utc_input():
    """Input mang tzinfo khác UTC phải được quy đổi, không cắt theo giờ địa phương."""
    vn = timezone(timedelta(hours=7))
    # 02:00 ngày 23/07 giờ VN = 19:00 ngày 22/07 UTC
    start, _ = utc_day_bounds(datetime(2026, 7, 23, 2, 0, 0, tzinfo=vn))
    assert start == datetime(2026, 7, 22, 0, 0, 0)


@pytest.mark.asyncio
async def test_sum_model_calls_uses_sum_not_count():
    """Budget đếm LƯỢT GỌI, không phải số request — mode A có thể tốn 2 lượt/request."""
    session = _RecordingSession()
    await ChatLogRepository(session).sum_model_calls_today()

    sql = _sql(session.statements[0]).lower()
    assert "sum(" in sql, "phải SUM(model_calls), không phải COUNT(*)"
    assert "model_calls" in sql
    assert "coalesce" in sql, "bảng rỗng phải trả 0, không phải NULL"
