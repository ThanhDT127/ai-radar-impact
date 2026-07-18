"""Data access cho bảng subscribers (delivery-telegram)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriber import Subscriber


class SubscriberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, chat_id: int) -> Subscriber | None:
        result = await self.session.execute(
            select(Subscriber).where(Subscriber.chat_id == chat_id)
        )
        return result.scalar_one_or_none()

    async def ensure_exists(self, chat_id: int, display_name: str | None = None) -> Subscriber:
        """Upsert từ /start: tạo bản ghi (roles=[], active) nếu chưa có.

        Không auto-reactivate người đã /unsubscribe — chỉ /subscribe mới bật lại.
        """
        sub = await self.get(chat_id)
        if sub is None:
            sub = Subscriber(chat_id=chat_id, roles=[], active=True, display_name=display_name)
            self.session.add(sub)
        elif display_name and sub.display_name != display_name:
            sub.display_name = display_name
        await self.session.commit()
        return sub

    async def set_roles(self, chat_id: int, roles: list[str], display_name: str | None = None) -> Subscriber:
        """Lưu lựa chọn /subscribe; đăng ký lại cũng bật active."""
        sub = await self.get(chat_id)
        if sub is None:
            sub = Subscriber(chat_id=chat_id, roles=roles, active=True, display_name=display_name)
            self.session.add(sub)
        else:
            sub.roles = roles
            sub.active = True
            if display_name:
                sub.display_name = display_name
        await self.session.commit()
        return sub

    async def deactivate(self, chat_id: int) -> bool:
        """/unsubscribe: active=false, giữ bản ghi. Trả False nếu chưa từng đăng ký."""
        sub = await self.get(chat_id)
        if sub is None:
            return False
        sub.active = False
        await self.session.commit()
        return True

    async def list_active(self) -> list[Subscriber]:
        """Subscriber đang nhận tin (active và đã chọn ít nhất 1 role)."""
        result = await self.session.execute(
            select(Subscriber).where(Subscriber.active == True)  # noqa: E712
        )
        return [s for s in result.scalars().all() if s.roles]
