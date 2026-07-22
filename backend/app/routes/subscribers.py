"""Quản lý người nhận bản tin + hủy nhận.

MVP KHÔNG yêu cầu xác thực (chạy nội bộ). Siết sau bằng
`dependencies=[Depends(verify_admin_key)]` như `routes/admin.py`.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.subscriber_repo import SubscriberRepository
from app.schemas.subscriber import SubscriberCreate, SubscriberItem, SubscriberUpdate

router = APIRouter(prefix="/api/v1/subscribers", tags=["subscribers"])

# Hủy nhận nằm ngoài prefix: link đi trong email, giữ đường dẫn ngắn và ổn định.
unsubscribe_router = APIRouter(prefix="/api/v1/unsubscribe", tags=["subscribers"])


@router.get("", response_model=list[SubscriberItem])
async def list_subscribers(session: AsyncSession = Depends(get_session)):
    return await SubscriberRepository(session).list_all()


@router.post("", response_model=SubscriberItem, status_code=201)
async def create_subscriber(
    payload: SubscriberCreate, session: AsyncSession = Depends(get_session)
):
    repo = SubscriberRepository(session)
    if await repo.get_by_email(payload.email):
        raise HTTPException(status_code=409, detail="Địa chỉ email này đã đăng ký")
    return await repo.create(
        email=payload.email, roles=payload.roles, display_name=payload.display_name
    )


@router.patch("/{subscriber_id}", response_model=SubscriberItem)
async def update_subscriber(
    subscriber_id: uuid.UUID,
    payload: SubscriberUpdate,
    session: AsyncSession = Depends(get_session),
):
    sub = await SubscriberRepository(session).update(
        subscriber_id,
        roles=payload.roles,
        active=payload.active,
        display_name=payload.display_name,
    )
    if sub is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người nhận")
    return sub


@router.delete("/{subscriber_id}", status_code=204)
async def delete_subscriber(
    subscriber_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    if not await SubscriberRepository(session).delete(subscriber_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy người nhận")


_UNSUBSCRIBE_PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>Hủy nhận bản tin AI Radar</title></head>
<body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:520px;margin:64px auto;padding:0 16px;">
<h2 style="color:#111827;">{heading}</h2>
<p style="color:#374151;line-height:1.6;">{body}</p>
{form}
</body></html>"""

_CONFIRM_FORM = """<form method="post">
<button type="submit" style="padding:10px 18px;background:#dc2626;color:#fff;border:0;border-radius:6px;cursor:pointer;">
Xác nhận hủy nhận</button></form>"""


@unsubscribe_router.get("", response_class=HTMLResponse)
async def unsubscribe_page(
    token: str = Query(...), session: AsyncSession = Depends(get_session)
):
    sub = await SubscriberRepository(session).get_by_unsubscribe_token(token)
    if sub is None:
        raise HTTPException(status_code=404, detail="Link hủy nhận không hợp lệ")
    if not sub.active:
        return HTMLResponse(
            _UNSUBSCRIBE_PAGE.format(
                heading="Bạn đã hủy nhận rồi",
                body=f"Địa chỉ {sub.email} hiện không nhận bản tin AI Radar.",
                form="",
            )
        )
    return HTMLResponse(
        _UNSUBSCRIBE_PAGE.format(
            heading="Hủy nhận bản tin AI Radar",
            body=f"Bạn có chắc muốn ngừng nhận bản tin ở địa chỉ {sub.email}?",
            form=_CONFIRM_FORM,
        )
    )


@unsubscribe_router.post("", response_class=HTMLResponse)
async def unsubscribe_confirm(
    token: str = Query(...), session: AsyncSession = Depends(get_session)
):
    """Cũng phục vụ one-click unsubscribe của Gmail (`List-Unsubscribe-Post`)."""
    sub = await SubscriberRepository(session).deactivate_by_token(token)
    if sub is None:
        raise HTTPException(status_code=404, detail="Link hủy nhận không hợp lệ")
    return HTMLResponse(
        _UNSUBSCRIBE_PAGE.format(
            heading="Đã hủy nhận",
            body=f"Địa chỉ {sub.email} sẽ không nhận bản tin AI Radar nữa.",
            form="",
        )
    )
