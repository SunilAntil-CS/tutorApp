"""
Tenant context middleware: extracts tenant from request and sets request-scoped context.

// Like a Spring OncePerRequestFilter that populates MDC
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.tenant_context import set_tenant_id, reset_tenant_id

# Header name for tenant extraction (Priority 1).
X_TENANT_ID = "X-Tenant-ID"
# Default when no tenant is found (landing pages, health checks).
DEFAULT_TENANT_ID = "public"


def _extract_tenant_id(request: Request) -> str:
    """Priority 1: X-Tenant-ID header. Priority 2: subdomain (placeholder for later)."""
    header_value = request.headers.get(X_TENANT_ID)
    if header_value and header_value.strip():
        return header_value.strip()
    # Priority 2: Subdomain (e.g. school-a.tutorapp.com -> school-a). Refine later.
    host = request.headers.get("host") or ""
    if "." in host:
        subdomain = host.split(".", 1)[0].strip()
        if subdomain and subdomain.lower() not in ("www", "api"):
            return subdomain
    return DEFAULT_TENANT_ID


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Sets tenant context for each request and resets it after the request.

    // Like a Spring OncePerRequestFilter that populates MDC
    """

    async def dispatch(self, request: Request, call_next):
        tenant_id = _extract_tenant_id(request)
        # token is like a try-with-resources handle to clean up ThreadLocal
        token = set_tenant_id(tenant_id)
        try:
            # dispatch is equivalent to chain.doFilter()
            response = await call_next(request)
            return response
        finally:
            reset_tenant_id(token)
