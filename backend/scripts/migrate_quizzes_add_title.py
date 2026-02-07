# One-off migration: add quizzes.title (and create questions table if missing).
# Run once when upgrading from old Quiz schema (questions_json) to new (title + Question table).
#
#   docker compose exec backend python -m scripts.migrate_quizzes_add_title
#
# Or from backend dir: python -m scripts.migrate_quizzes_add_title

import asyncio
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings

_engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)


async def migrate() -> None:
    async with _engine.begin() as conn:
        # Add title if quizzes was created with old schema (questions_json only)
        await conn.execute(text("""
            ALTER TABLE quizzes
            ADD COLUMN IF NOT EXISTS title VARCHAR DEFAULT 'Quiz'
        """))
        # Ensure existing rows have a value (IF NOT EXISTS doesn't set existing NULLs in some PG versions)
        await conn.execute(text("""
            UPDATE quizzes SET title = 'Quiz' WHERE title IS NULL
        """))
    print("Migration done: quizzes.title added/updated.")
    await _engine.dispose()


def main() -> None:
    asyncio.run(migrate())


if __name__ == "__main__":
    main()
