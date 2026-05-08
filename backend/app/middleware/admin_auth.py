"""Admin API key authentication dependency."""

from fastapi import Header, HTTPException

from app.config import settings


async def verify_admin_key(authorization: str = Header(default="")) -> None:
    """FastAPI dependency — raise 401 if Bearer token does not match ADMIN_API_KEY."""
    expected = f"Bearer {settings.admin_api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
