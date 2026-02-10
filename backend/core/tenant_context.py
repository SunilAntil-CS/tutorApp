"""
Request-scoped context storage for the current tenant in a multi-tenant SaaS.

This module provides an async-safe, thread-safe way to store and retrieve the
tenant_id for the duration of a single request using contextvars. Middleware
sets the tenant; services and repositories read it without passing it through
every layer.
"""

from contextvars import ContextVar, Token

_tenant_context: ContextVar[str] = ContextVar(
    "tenant_context",
    default="unknown",
)


def set_tenant_id(tenant_id: str) -> Token[str]:
    """Set the current request's tenant ID in context. Returns a token for cleanup via reset_tenant_id."""
    return _tenant_context.set(tenant_id)


def reset_tenant_id(token: Token[str]) -> None:
    """Restore the context to its previous value (e.g. after request completes)."""
    _tenant_context.reset(token)


def get_tenant_id() -> str:
    """Return the current request's tenant ID, or 'unknown' if not set."""
    return _tenant_context.get()
