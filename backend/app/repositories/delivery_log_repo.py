"""Data access cho bảng delivery_log (chống gửi trùng, audit)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_log import DeliveryLog


class DeliveryLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def sent_insight_ids(
        self, subscriber_id: uuid.UUID, kind: str, insight_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Trong danh sách ứng viên, những insight nào đã gửi cho người này rồi."""
        if not insight_ids:
            return set()
        result = await self.session.execute(
            select(DeliveryLog.insight_id).where(
                DeliveryLog.subscriber_id == subscriber_id,
                DeliveryLog.kind == kind,
                DeliveryLog.insight_id.in_(insight_ids),
            )
        )
        return set(result.scalars().all())

    async def sent_within(self, subscriber_id: uuid.UUID, kind: str, hours: int) -> bool:
        """Người này đã nhận bản tin trong `hours` giờ gần đây chưa?

        Chốt chặn theo chu kỳ: vì `log_sent` chỉ ghi tin THỰC SỰ gửi (không ghi phần bị
        loại vì trần), lần chạy thừa trong cùng kỳ sẽ lấy 3 tin xếp hạng kế tiếp và gửi
        tiếp — unique constraint không chặn được vì đó là tin khác.

        So sánh hoàn toàn trong SQL bằng `now()` của DB để không lẫn với `datetime.utcnow()`
        phía Python.
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(DeliveryLog)
            .where(
                DeliveryLog.subscriber_id == subscriber_id,
                DeliveryLog.kind == kind,
                DeliveryLog.sent_at > func.now() - func.make_interval(0, 0, 0, 0, hours),
            )
        )
        return result.scalar_one() > 0

    async def log_sent(
        self, insight_ids: list[uuid.UUID], subscriber_id: uuid.UUID, kind: str
    ) -> None:
        """Ghi log các insight ĐÃ GỬI; ON CONFLICT DO NOTHING để idempotent.

        Chỉ gọi cho tin thực sự nằm trong email — tin bị loại vì trần số lượng không
        ghi log, để còn quyền cạnh tranh ở kỳ kế tiếp.
        """
        if not insight_ids:
            return
        stmt = pg_insert(DeliveryLog).values(
            [
                {
                    "id": uuid.uuid4(),
                    "insight_id": iid,
                    "subscriber_id": subscriber_id,
                    "kind": kind,
                }
                for iid in insight_ids
            ]
        ).on_conflict_do_nothing(constraint="uq_delivery_log_insight_subscriber_kind")
        await self.session.execute(stmt)
        await self.session.commit()
