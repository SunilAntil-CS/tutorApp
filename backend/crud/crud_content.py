"""Content data access: async select/insert for Books, Chapters, Lessons, Quizzes."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.content import Book, Chapter, Lesson, LessonProgress, Quiz


class CRUDContent:
    """Async CRUD for content entities. No business logic; returns ORM models."""

    # ----- Books -----

    async def get_books(self, session: AsyncSession) -> list[Book]:
        """Select all books, ordered by grade then title."""
        stmt = select(Book).order_by(Book.grade, Book.title)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_book_by_id(self, session: AsyncSession, book_id: UUID) -> Book | None:
        """Select a single book by id."""
        stmt = select(Book).where(Book.id == book_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_book(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        title: str,
        grade: int,
        subject: str,
        cover_image: str | None = None,
    ) -> Book:
        """Insert a book."""
        book = Book(tenant_id=tenant_id, title=title, grade=grade, subject=subject, cover_image=cover_image)
        session.add(book)
        await session.commit()
        await session.refresh(book)
        return book

    # ----- Chapters -----

    async def get_chapters_by_book_id(self, session: AsyncSession, book_id: UUID) -> list[Chapter]:
        """Select chapters for a book, ordered by sequence_number."""
        stmt = select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.sequence_number)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_chapter(
        self,
        session: AsyncSession,
        *,
        book_id: UUID,
        tenant_id: str,
        sequence_number: int,
        title: str,
    ) -> Chapter:
        """Insert a chapter."""
        chapter = Chapter(book_id=book_id, tenant_id=tenant_id, sequence_number=sequence_number, title=title)
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)
        return chapter

    # ----- Lessons -----

    async def get_lessons_by_chapter_id(self, session: AsyncSession, chapter_id: UUID) -> list[Lesson]:
        """Select lessons for a chapter (order can be by id or a future sequence field)."""
        stmt = select(Lesson).where(Lesson.chapter_id == chapter_id).order_by(Lesson.title)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_quick_notes(
        self, session: AsyncSession, subject: str | None = None
    ) -> list[Lesson]:
        """Select standalone lessons (Quick Concepts) where is_quick_note is True. Optional filter by subject. Order by title."""
        stmt = select(Lesson).where(Lesson.is_quick_note == True)
        if subject is not None:
            stmt = stmt.where(Lesson.subject == subject)
        stmt = stmt.order_by(Lesson.title)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_lesson_by_id(self, session: AsyncSession, lesson_id: UUID) -> Lesson | None:
        """Select a single lesson by id."""
        stmt = select(Lesson).where(Lesson.id == lesson_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_lesson(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        title: str,
        chapter_id: UUID | None = None,
        subject: str | None = None,
        is_quick_note: bool = False,
        video_id: str | None = None,
        pdf_url: str | None = None,
        duration_seconds: int | None = None,
        is_free: bool = True,
    ) -> Lesson:
        """Insert a lesson (book chapter lesson or standalone quick note)."""
        lesson = Lesson(
            tenant_id=tenant_id,
            title=title,
            chapter_id=chapter_id,
            subject=subject,
            is_quick_note=is_quick_note,
            video_id=video_id,
            pdf_url=pdf_url,
            duration_seconds=duration_seconds,
            is_free=is_free,
        )
        session.add(lesson)
        await session.commit()
        await session.refresh(lesson)
        return lesson

    # ----- Quizzes -----

    async def get_quiz_by_lesson_id(self, session: AsyncSession, lesson_id: UUID) -> Quiz | None:
        """Select the quiz for a lesson (if any)."""
        stmt = select(Quiz).where(Quiz.lesson_id == lesson_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_quiz(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        lesson_id: UUID,
        title: str = "Quiz",
    ) -> Quiz:
        """Insert a quiz."""
        quiz = Quiz(tenant_id=tenant_id, lesson_id=lesson_id, title=title)
        session.add(quiz)
        await session.commit()
        await session.refresh(quiz)
        return quiz

    # ----- Lesson progress (for quiz completion) -----

    async def get_lesson_progress(
        self, session: AsyncSession, user_id: UUID, lesson_id: UUID
    ) -> LessonProgress | None:
        """Get progress for a user on a lesson."""
        stmt = select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id == lesson_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_lesson_progress(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        user_id: UUID,
        lesson_id: UUID,
        is_completed: bool = False,
        quiz_score: int | None = None,
    ) -> LessonProgress:
        """Insert or update one row per user per lesson."""
        existing = await self.get_lesson_progress(session, user_id, lesson_id)
        if existing:
            existing.is_completed = is_completed
            if quiz_score is not None:
                existing.quiz_score = quiz_score
            await session.commit()
            await session.refresh(existing)
            return existing
        row = LessonProgress(
            tenant_id=tenant_id,
            user_id=user_id,
            lesson_id=lesson_id,
            is_completed=is_completed,
            quiz_score=quiz_score,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


crud_content = CRUDContent()
