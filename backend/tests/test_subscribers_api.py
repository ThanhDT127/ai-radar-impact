"""API quản lý người nhận + hủy nhận.

Suite không có hạ tầng test DB (xem `test_insight_count_queries.py`), nên test gọi thẳng
handler với repository giả — đủ khoá hành vi HTTP mà không cần Postgres.
"""

import uuid

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.routes import subscribers as routes
from app.schemas.subscriber import SubscriberCreate, SubscriberUpdate


class FakeSubscriber:
    def __init__(self, email, roles=None, active=True, token="tok-1"):
        self.id = uuid.uuid4()
        self.email = email
        self.roles = roles or []
        self.display_name = None
        self.active = active
        self.unsubscribe_token = token


class FakeRepo:
    """Thay `SubscriberRepository`; chỉ giữ những hành vi handler thực sự dùng.

    Store để ở mức CLASS: mỗi handler tự tạo một repository mới nên state phải sống
    ngoài instance. Fixture xoá trước mỗi test.
    """

    rows: list[FakeSubscriber] = []

    def __init__(self, session=None):
        pass

    async def get_by_email(self, email):
        return next((s for s in self.rows if s.email == email.strip().lower()), None)

    async def get_by_id(self, subscriber_id):
        return next((s for s in self.rows if s.id == subscriber_id), None)

    async def get_by_unsubscribe_token(self, token):
        return next((s for s in self.rows if s.unsubscribe_token == token), None)

    async def list_all(self):
        return list(self.rows)

    async def create(self, email, roles, display_name=None):
        sub = FakeSubscriber(email.strip().lower(), roles)
        sub.display_name = display_name
        self.rows.append(sub)
        return sub

    async def update(self, subscriber_id, roles=None, active=None, display_name=None):
        sub = await self.get_by_id(subscriber_id)
        if sub is None:
            return None
        if roles is not None:
            sub.roles = roles
        if active is not None:
            sub.active = active
        return sub

    async def delete(self, subscriber_id):
        sub = await self.get_by_id(subscriber_id)
        if sub is None:
            return False
        self.rows.remove(sub)
        return True

    async def deactivate_by_token(self, token):
        sub = await self.get_by_unsubscribe_token(token)
        if sub is None:
            return None
        sub.active = False
        return sub


@pytest.fixture(autouse=True)
def fake_repo(monkeypatch):
    FakeRepo.rows = []
    monkeypatch.setattr(routes, "SubscriberRepository", FakeRepo)
    return FakeRepo


# ── Schema ───────────────────────────────────────────────────────────────────


def test_email_is_normalized_to_lowercase():
    assert SubscriberCreate(email="  An.Nguyen@RangDong.VN ", roles=["Dev"]).email == (
        "an.nguyen@rangdong.vn"
    )


@pytest.mark.parametrize("bad", ["khong-co-a-cong", "thieu@domain", "@rangdong.vn", "a b@x.vn"])
def test_invalid_email_rejected(bad):
    with pytest.raises(ValidationError):
        SubscriberCreate(email=bad, roles=["Dev"])


def test_role_outside_allowed_set_rejected():
    """`roles` phải thuộc 9 ALLOWED_ROLES, KHÔNG phải 13 target_roles của Source."""
    with pytest.raises(ValidationError) as exc:
        SubscriberCreate(email="a@x.vn", roles=["Marketing"])
    assert "Marketing" in str(exc.value)


def test_department_taxonomy_is_not_accepted():
    """`Engineering` là target_roles của Source — không được lọt vào Subscriber.roles."""
    with pytest.raises(ValidationError):
        SubscriberCreate(email="a@x.vn", roles=["Engineering"])


def test_update_allows_omitting_roles():
    assert SubscriberUpdate(active=False).roles is None


def test_update_still_validates_roles_when_given():
    with pytest.raises(ValidationError):
        SubscriberUpdate(roles=["Marketing"])


# ── CRUD ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_then_list():
    created = await routes.create_subscriber(
        SubscriberCreate(email="a@x.vn", roles=["Security"]), session=None
    )
    assert created.email == "a@x.vn"
    assert [s.email for s in await routes.list_subscribers(session=None)] == ["a@x.vn"]


@pytest.mark.asyncio
async def test_duplicate_email_differing_case_rejected():
    await routes.create_subscriber(SubscriberCreate(email="An@X.vn", roles=["Dev"]), session=None)
    with pytest.raises(HTTPException) as exc:
        await routes.create_subscriber(
            SubscriberCreate(email="an@x.vn", roles=["Security"]), session=None
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_unknown_id_returns_404():
    with pytest.raises(HTTPException) as exc:
        await routes.update_subscriber(uuid.uuid4(), SubscriberUpdate(active=False), session=None)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_unknown_id_returns_404():
    with pytest.raises(HTTPException) as exc:
        await routes.delete_subscriber(uuid.uuid4(), session=None)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_toggle_active():
    sub = await routes.create_subscriber(
        SubscriberCreate(email="a@x.vn", roles=["Dev"]), session=None
    )
    updated = await routes.update_subscriber(sub.id, SubscriberUpdate(active=False), session=None)
    assert updated.active is False


# ── Hủy nhận ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unsubscribe_page_bad_token_returns_404():
    with pytest.raises(HTTPException) as exc:
        await routes.unsubscribe_page(token="khong-ton-tai", session=None)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_unsubscribe_post_deactivates_without_deleting():
    await routes.create_subscriber(SubscriberCreate(email="a@x.vn", roles=["Dev"]), session=None)
    FakeRepo.rows[0].unsubscribe_token = "tok-abc"

    response = await routes.unsubscribe_confirm(token="tok-abc", session=None)

    assert response.status_code == 200
    assert FakeRepo.rows[0].active is False
    assert len(FakeRepo.rows) == 1  # giữ bản ghi để không mất lịch sử delivery_log


@pytest.mark.asyncio
async def test_unsubscribe_post_bad_token_returns_404():
    with pytest.raises(HTTPException) as exc:
        await routes.unsubscribe_confirm(token="sai", session=None)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_unsubscribe_page_shows_confirm_form_then_done():
    await routes.create_subscriber(SubscriberCreate(email="a@x.vn", roles=["Dev"]), session=None)
    FakeRepo.rows[0].unsubscribe_token = "tok-abc"

    before = (await routes.unsubscribe_page(token="tok-abc", session=None)).body.decode()
    assert "form" in before and "a@x.vn" in before

    await routes.unsubscribe_confirm(token="tok-abc", session=None)
    after = (await routes.unsubscribe_page(token="tok-abc", session=None)).body.decode()
    assert "Bạn đã hủy nhận rồi" in after
