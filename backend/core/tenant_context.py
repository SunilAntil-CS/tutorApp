"""
Request-scoped context storage for the current tenant in a multi-tenant SaaS.

This module provides an async-safe, thread-safe way to store and retrieve the
tenant_id for the duration of a single request using contextvars. Middleware
sets the tenant; services and repositories read it without passing it through
every layer.
"""

from contextvars import ContextVar

_tenant_context: ContextVar[str] = ContextVar(
    "tenant_context",
    default="unknown",
)


def set_tenant_id(tenant_id: str) -> None:
    """Set the current request's tenant ID in context."""
    _tenant_context.set(tenant_id)


def get_tenant_id() -> str:
    """Return the current request's tenant ID, or 'unknown' if not set."""
    return _tenant_context.get()
