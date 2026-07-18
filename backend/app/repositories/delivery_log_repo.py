"""Data access cho bảng delivery_log (chống gửi trùng, audit)."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_log import DeliveryLog


class DeliveryLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def sent_insight_ids(
        self, chat_id: int, kind: str, insight_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Trong danh sách ứng viên, những insight nào đã gửi cho chat này rồi."""
        if not insight_ids:
            return set()
        result = await self.session.execute(
            select(DeliveryLog.insight_id).where(
                DeliveryLog.chat_id == chat_id,
                DeliveryLog.kind == kind,
                DeliveryLog.insight_id.in_(insight_ids),
            )
        )
        return set(result.scalars().all())

    async def count_alerts_last_hour(self, chat_id: int) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=1)
        result = await self.session.execute(
            select(func.count())
            .select_from(DeliveryLog)
            .where(
                DeliveryLog.chat_id == chat_id,
                DeliveryLog.kind == "alert",
                DeliveryLog.sent_at >= cutoff,
            )
        )
        return result.scalar_one()

    async def log_sent(self, insight_ids: list[uuid.UUID], chat_id: int, kind: str) -> None:
        """Ghi log các insight đã gửi; ON CONFLICT DO NOTHING để idempotent."""
        if not insight_ids:
            return
        stmt = pg_insert(DeliveryLog).values(
            [
                {"id": uuid.uuid4(), "insight_id": iid, "chat_id": chat_id, "kind": kind}
                for iid in insight_ids
            ]
        ).on_conflict_do_nothing(constraint="uq_delivery_log_insight_chat_kind")
        await self.session.execute(stmt)
        await self.session.commit()
