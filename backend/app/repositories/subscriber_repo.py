"""Data access cho bảng subscribers (người nhận bản tin qua email)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriber import Subscriber


def normalize_email(email: str) -> str:
    """Chuẩn hoá địa chỉ để so trùng không phụ thuộc hoa/thường và khoảng trắng."""
    return email.strip().lower()


class SubscriberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, subscriber_id: uuid.UUID) -> Subscriber | None:
        return await self.session.get(Subscriber, subscriber_id)

    async def get_by_email(self, email: str) -> Subscriber | None:
        result = await self.session.execute(
            select(Subscriber).where(Subscriber.email == normalize_email(email))
        )
        return result.scalar_one_or_none()

    async def get_by_unsubscribe_token(self, token: str) -> Subscriber | None:
        result = await self.session.execute(
            select(Subscriber).where(Subscriber.unsubscribe_token == token)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Subscriber]:
        result = await self.session.execute(select(Subscriber).order_by(Subscriber.created_at))
        return list(result.scalars().all())

    async def list_active(self) -> list[Subscriber]:
        """Người đang nhận bản tin: active và đã chọn ít nhất 1 role."""
        result = await self.session.execute(
            select(Subscriber).where(Subscriber.active == True)  # noqa: E712
        )
        return [s for s in result.scalars().all() if s.roles]

    async def create(
        self, email: str, roles: list[str], display_name: str | None = None
    ) -> Subscriber:
        sub = Subscriber(
            email=normalize_email(email),
            roles=roles,
            display_name=display_name,
            active=True,
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def update(
        self,
        subscriber_id: uuid.UUID,
        roles: list[str] | None = None,
        active: bool | None = None,
        display_name: str | None = None,
    ) -> Subscriber | None:
        sub = await self.get_by_id(subscriber_id)
        if sub is None:
            return None
        if roles is not None:
            sub.roles = roles
        if active is not None:
            sub.active = active
        if display_name is not None:
            sub.display_name = display_name
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def delete(self, subscriber_id: uuid.UUID) -> bool:
        sub = await self.get_by_id(subscriber_id)
        if sub is None:
            return False
        await self.session.delete(sub)
        await self.session.commit()
        return True

    async def deactivate_by_token(self, token: str) -> Subscriber | None:
        """Hủy nhận từ link trong email — giữ bản ghi, chỉ tắt active."""
        sub = await self.get_by_unsubscribe_token(token)
        if sub is None:
            return None
        sub.active = False
        await self.session.commit()
        return sub
