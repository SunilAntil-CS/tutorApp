# Seed the local database with sample content (Book -> Chapter -> Lesson).
#
# Run inside Docker (from repo root; container workdir is /app = backend contents):
#   docker compose exec backend python -m scripts.seed_content
#
# Run locally (from backend directory):
#   cd backend && python -m scripts.seed_content

import asyncio
import sys
from pathlib import Path

# Ensure backend root is on path so "config" and "models" resolve
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import settings
from models.content import Book, Chapter, Lesson, Question, Quiz, Tenant

DEFAULT_TENANT_ID = "default"
# Second tenant for testing tenant isolation (GET /books with X-Tenant-ID: default vs school-b).
SECOND_TENANT_ID = "school-b"


# Use same engine config as main app; models already registered via import above
_engine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
)
_session_maker = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _book_exists(session: AsyncSession, title: str) -> bool:
    stmt = select(Book).where(Book.title == title)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _get_lesson_by_title(session: AsyncSession, title: str) -> Lesson | None:
    stmt = select(Lesson).where(Lesson.title == title)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _quiz_exists_for_lesson(session: AsyncSession, lesson_id) -> bool:
    stmt = select(Quiz).where(Quiz.lesson_id == lesson_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _quick_note_exists(session: AsyncSession, title: str) -> bool:
    stmt = select(Lesson).where(Lesson.title == title, Lesson.is_quick_note == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _seed_quick_notes(session: AsyncSession) -> None:
    """Create sample Quick Concept lessons (standalone, no chapter)."""
    if await _quick_note_exists(session, "What is a Chemical Equation?"):
        print("Quick notes already seeded.")
        return

    quick_notes = [
        Lesson(
            tenant_id=DEFAULT_TENANT_ID,
            chapter_id=None,
            title="What is a Chemical Equation?",
            subject="Science",
            is_quick_note=True,
            video_id=None,
            pdf_url="https://drive.google.com/uc?export=download&id=1AFewMW0uS7QvqgoqTKp5wQd5zzDIorca",
            duration_seconds=180,
        ),
        Lesson(
            tenant_id=DEFAULT_TENANT_ID,
            chapter_id=None,
            title="Introduction to Light – Reflection",
            subject="Science",
            is_quick_note=True,
            video_id="Xf_VZ8GxU1Y",
            pdf_url=None,
            duration_seconds=300,
        ),
    ]
    for lesson in quick_notes:
        session.add(lesson)
    await session.commit()
    print("Seeded: 2 Quick Notes (Science).")


async def _seed_quiz_for_lesson(session: AsyncSession, lesson: Lesson) -> None:
    """Create Quiz and 3 Questions for 'Balancing Chemical Equations' if not already present."""
    if await _quiz_exists_for_lesson(session, lesson.id):
        print("Quiz already exists for this lesson.")
        return

    quiz = Quiz(tenant_id=lesson.tenant_id, lesson_id=lesson.id, title="Balancing Equations Check")
    session.add(quiz)
    await session.flush()

    questions = [
        Question(
            tenant_id=lesson.tenant_id,
            quiz_id=quiz.id,
            text="What is the coefficient of H2 in 2H2 + O2 -> 2H2O?",
            option_a="1",
            option_b="2",
            option_c="3",
            option_d="4",
            correct_answer="B",
        ),
        Question(
            tenant_id=lesson.tenant_id,
            quiz_id=quiz.id,
            text="Is mass conserved in a chemical reaction?",
            option_a="Yes",
            option_b="No",
            option_c="Maybe",
            option_d="Only in space",
            correct_answer="A",
        ),
        Question(
            tenant_id=lesson.tenant_id,
            quiz_id=quiz.id,
            text="What implies a gas is evolved?",
            option_a="Down Arrow",
            option_b="Up Arrow",
            option_c="Triangle",
            option_d="Circle",
            correct_answer="B",
        ),
    ]
    for q in questions:
        session.add(q)

    await session.commit()
    print("Seeded: Quiz 'Balancing Equations Check' with 3 questions.")


async def _ensure_default_tenant(session: AsyncSession) -> None:
    """Ensure default tenant exists (for seed and local dev)."""
    result = await session.execute(select(Tenant).where(Tenant.id == DEFAULT_TENANT_ID))
    if result.scalar_one_or_none() is None:
        session.add(Tenant(id=DEFAULT_TENANT_ID, name="Tutor App", config_json="{}"))
        await session.flush()


async def _ensure_second_tenant(session: AsyncSession) -> None:
    """Ensure second tenant + one book exist (for testing tenant isolation in CRUD/Swagger)."""
    result = await session.execute(select(Tenant).where(Tenant.id == SECOND_TENANT_ID))
    if result.scalar_one_or_none() is not None:
        return
    session.add(Tenant(id=SECOND_TENANT_ID, name="School B", config_json="{}"))
    await session.flush()

    if await _book_exists(session, "Math Class 9"):
        return
    book = Book(
        tenant_id=SECOND_TENANT_ID,
        title="Math Class 9",
        subject="Math",
        grade=9,
    )
    session.add(book)
    await session.flush()
    session.add(
        Chapter(
            book_id=book.id,
            tenant_id=SECOND_TENANT_ID,
            sequence_number=1,
            title="Number Systems",
        )
    )
    await session.flush()
    print("Seeded: tenant 'school-b' with book 'Math Class 9' (for isolation testing).")


async def seed() -> None:
    async with _session_maker() as session:
        await _ensure_default_tenant(session)
        await _ensure_second_tenant(session)

        if not await _book_exists(session, "Science Class 10"):
            book = Book(
                tenant_id=DEFAULT_TENANT_ID,
                title="Science Class 10",
                subject="Science",
                grade=10,
                cover_image="https://placehold.co/600x400",
            )
            session.add(book)
            await session.flush()

            chapter = Chapter(
                book_id=book.id,
                tenant_id=DEFAULT_TENANT_ID,
                title="Chemical Reactions",
                sequence_number=1,
            )
            session.add(chapter)
            await session.flush()

            lesson = Lesson(
                tenant_id=DEFAULT_TENANT_ID,
                chapter_id=chapter.id,
                title="Balancing Chemical Equations",
                video_id="dQw4w9WgXcQ",
                duration_seconds=600,
            )
            session.add(lesson)
            await session.commit()
            print("Seeded: Book 'Science Class 10', Chapter 'Chemical Reactions', Lesson 'Balancing Chemical Equations'.")

        lesson = await _get_lesson_by_title(session, "Balancing Chemical Equations")
        if not lesson:
            print("Lesson 'Balancing Chemical Equations' not found. Run seed without quiz first.")
            return

        await _seed_quiz_for_lesson(session, lesson)

        await _seed_quick_notes(session)

        # Verify: print counts so you know data is in the DB the script connected to
        r_books = await session.execute(select(Book))
        r_lessons = await session.execute(select(Lesson))
        r_quizzes = await session.execute(select(Quiz))
        r_questions = await session.execute(select(Question))
        books = list(r_books.scalars().all())
        lessons = list(r_lessons.scalars().all())
        quizzes = list(r_quizzes.scalars().all())
        questions = list(r_questions.scalars().all())
        print(f"Verification: {len(books)} books, {len(lessons)} lessons, {len(quizzes)} quizzes, {len(questions)} questions.")
        print(f"DB: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    await _engine.dispose()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
