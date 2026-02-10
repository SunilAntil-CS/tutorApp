"""
Alembic env: use config from .env (pydantic-settings), SQLModel.metadata for autogenerate.
Run from backend dir: alembic upgrade head | alembic revision --autogenerate -m "msg"
"""
import sys
from pathlib import Path

# Ensure backend root is on path
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from config import settings

# Import all models so SQLModel.metadata has every table (for autogenerate)
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

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url() -> str:
    """Database URL from app config (.env). Sync URL for Alembic."""
    return settings.database_url_sync


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode: generate SQL script only."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode: connect to DB and apply."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
