"""Dependency injection: DB session and tenant gatekeeper for routers."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID

from async_lru import alru_cache  # type: ignore[import-untyped]
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.tenant_context import get_tenant_id
from logging_config import get_logger
from models.content import Tenant

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

log = get_logger("auth")

# Routes that do not require tenant validation (e.g. health, docs).
PUBLIC_PATHS = ["/health", "/docs", "/openapi.json", "/redoc"]

# Set by main lifespan so the cached tenant lookup can create its own session.
_session_maker: "async_sessionmaker[AsyncSession] | None" = None


def set_async_session_maker(session_maker: "async_sessionmaker[AsyncSession]") -> None:
    """Wire the async session maker for tenant lookup (called from main lifespan)."""
    global _session_maker
    _session_maker = session_maker


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session; router receives it via Depends(get_db)."""
    async with request.app.state.async_session_maker() as session:
        yield session


@alru_cache(maxsize=1000, ttl=300)
async def _get_tenant_from_db(tenant_id: str) -> Tenant | None:
    """
    Load tenant by ID from Postgres. Cached by tenant_id for 5 minutes.
    Uses its own session (session maker wired via set_async_session_maker).
    """
    log.info(f"🛑 DB MISS: Loading Tenant '{tenant_id}' from Postgres")
    if _session_maker is None:
        return None
    async with _session_maker() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()


async def get_current_tenant(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Tenant | None:
    """
    Tenant gatekeeper: validate tenant from context against DB, with caching.
    Returns None for public paths; raises 404 for unknown/invalid tenant_id.
    """
    if request.url.path in PUBLIC_PATHS:
        return None
    tenant_id = get_tenant_id()
    tenant = await _get_tenant_from_db(tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}",
        )
    return tenant


async def get_current_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> UUID:
    """Require X-User-Id header (placeholder until auth). Use for quiz submission."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id")
