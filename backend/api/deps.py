"""Dependency injection: DB session for routers."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session; router receives it via Depends(get_db)."""
    async with request.app.state.async_session_maker() as session:
        yield session


async def get_current_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> UUID:
    """Require X-User-Id header (placeholder until auth). Use for quiz submission."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id")
