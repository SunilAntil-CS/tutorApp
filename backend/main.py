from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
from sqlmodel import SQLModel

from config import settings

# Async engine with pool settings from config
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all SQLModel tables on startup; dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {"message": "Hello World", "app": settings.APP_NAME}


@app.get("/health")
async def health():
    """Verify application and database connectivity. Returns 503 if DB unreachable."""
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
