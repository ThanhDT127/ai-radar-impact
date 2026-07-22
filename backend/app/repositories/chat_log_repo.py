"""Data access cho bảng chat_logs — log request chat và counter budget."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_log import ChatLog


def utc_day_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Mốc đầu/cuối ngày theo UTC — tách ra để test được ranh giới nửa đêm.

    Dùng UTC cho khớp `RawDocumentRepository.count_analyzed_today()`; một bên UTC một
    bên giờ VN thì hai budget sẽ reset lệch nhau 7 tiếng.
    """
    now = now or datetime.now(timezone.utc)
    naive = now.astimezone(timezone.utc).replace(tzinfo=None) if now.tzinfo else now
    start = datetime(naive.year, naive.month, naive.day)
    return start, start + timedelta(days=1)


class ChatLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, mode: str, model_calls: int, citations_count: int, latency_ms: int
    ) -> None:
        """Ghi một bản ghi log. Gọi trong khối `finally` của service.

        Commit ngay: nếu request lỗi sau đó và session bị rollback thì lượt gọi đã tốn
        tiền vẫn phải nằm trong budget.
        """
        self.session.add(
            ChatLog(
                mode=mode,
                model_calls=model_calls,
                citations_count=citations_count,
                latency_ms=latency_ms,
            )
        )
        await self.session.commit()

    async def sum_model_calls_today(self, now: datetime | None = None) -> int:
        """Tổng lượt gọi model của chat trong ngày hôm nay (UTC) — dùng cho daily cap."""
        start, end = utc_day_bounds(now)
        result = await self.session.execute(
            select(func.coalesce(func.sum(ChatLog.model_calls), 0)).where(
                ChatLog.created_at >= start, ChatLog.created_at < end
            )
        )
        return int(result.scalar_one())
