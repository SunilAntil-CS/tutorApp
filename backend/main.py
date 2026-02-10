# Tutor App backend entrypoint
# Test comment - can be removed
import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager

import pdfkit
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config import settings
from logging_config import get_logger, setup_logging
from core.tenant_context import get_tenant_id
from middleware import TenantMiddleware

setup_logging()
log = get_logger("main")

# Import models so SQLModel.metadata knows about all tables
from models.content import (  # noqa: F401
    Book,
    Chapter,
    Concept,
    LearningEvent,
    Lesson,
    LessonProgress,
    Question,
    Quiz,
    Tenant,
    User,
)

# Async engine with pool settings from config
engine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Wire session maker; schema is managed by Alembic (alembic upgrade head)."""
    log.info("Starting up")
    app.state.async_session_maker = async_session_maker
    yield
    await engine.dispose()
    log.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# Request/response logging (log to file when LOG_FILE is set).
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        method = request.method
        path = request.url.path
        log.info("Request: %s %s", method, path)
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        log.info("Response: %s %s -> %s (%.1f ms)", method, path, response.status_code, elapsed)
        return response


app.add_middleware(RequestLoggingMiddleware)

# Tenant context: run first so logging and routes see tenant_id (last added = first to run).
app.add_middleware(TenantMiddleware)

# CORS: allow /docs (Swagger UI), /openapi.json, and all API routes from any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register API routers
from api.v1 import api_router  # noqa: E402
app.include_router(api_router)


def custom_openapi():
    """Ensure /docs and Swagger UI work: use relative server URL so the browser doesn't try 0.0.0.0."""
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=app.title,
        version=getattr(app, "version", "1.0"),
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    schema["servers"] = [{"url": "/"}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def root():
    return {"message": "Hello World", "app": settings.APP_NAME}


@app.get("/debug/tenant")
def debug_tenant():
    """Return current tenant_id from context (for testing TenantMiddleware). Remove or restrict in production."""
    return {"tenant_id": get_tenant_id()}


@app.get("/health")
async def health():
    """Verify application and database connectivity. Used by Docker/Coolify healthcheck; returns 503 if DB unreachable."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "app": settings.APP_NAME,
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "app": settings.APP_NAME,
                "detail": str(e),
            },
        )


def _openapi_static_html(schema: dict) -> str:
    """Build self-contained HTML for the OpenAPI schema (no CDN/network; safe for wkhtmltopdf in Docker)."""
    info = schema.get("info", {})
    title = info.get("title", "API")
    version = info.get("version", "")
    description = info.get("description", "") or ""
    paths = schema.get("paths", {})
    parts = [
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><style>",
        "body{font-family:system-ui,sans-serif;margin:2em;color:#333;}",
        "h1{color:#111;border-bottom:2px solid #333;}",
        "h2{color:#333;margin-top:1.5em;}",
        ".path{background:#f5f5f5;padding:0.5em 0.75em;margin:0.5em 0;border-radius:4px;}",
        ".method{display:inline-block;font-weight:bold;min-width:4em;margin-right:0.5em;}",
        ".get{color:#0a0;}.post{color:#07c;}.put{color:#a60;}.delete{color:#c00;}.patch{color:#a0a;}",
        "p{margin:0.25em 0;}",
        "</style></head><body>",
        f"<h1>{_escape(title)} {_escape(version)}</h1>",
    ]
    if description:
        parts.append(f"<p>{_escape(description)}</p>")
    parts.append("<h2>Endpoints</h2>")
    for path, path_item in sorted(paths.items()):
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch", "head", "options"):
                continue
            if not isinstance(op, dict):
                continue
            summary = op.get("summary", "")
            parts.append(
                f"<div class=\"path\"><span class=\"method {method.lower()}\">{method.upper()}</span>"
                f"{_escape(path)} — {_escape(summary)}</div>"
            )
    parts.append("</body></html>")
    return "".join(parts)


def _escape(s: str) -> str:
    """Escape HTML entities."""
    if not s:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@app.get("/docs/pdf")
async def docs_pdf():
    """Generate API documentation as a PDF using OpenAPI schema (static HTML, no network)."""
    schema = app.openapi()
    html = _openapi_static_html(schema)
    options = {"page-size": "A4"}
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None,
        lambda: pdfkit.from_string(html, False, options=options),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=tutor_app_api.pdf"},
    )
