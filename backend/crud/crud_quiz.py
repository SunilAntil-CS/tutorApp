"""Quiz and Question data access. Used by learning_service for display and grading."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.content import Question, Quiz


class QuizCRUD:
    """Async CRUD for Quiz and Question. No business logic; returns ORM models."""

    async def get_quiz_for_lesson(self, session: AsyncSession, lesson_id: UUID) -> tuple[Quiz | None, list[Question]]:
        """Fetch the quiz for a lesson and its questions (for public display; strip correct_answer in schema)."""
        stmt = select(Quiz).where(Quiz.lesson_id == lesson_id)
        result = await session.execute(stmt)
        quiz = result.scalar_one_or_none()
        if not quiz:
            return None, []
        # Load questions (order by id for stable ordering)
        q_stmt = select(Question).where(Question.quiz_id == quiz.id).order_by(Question.id)
        q_result = await session.execute(q_stmt)
        questions = list(q_result.scalars().all())
        return quiz, questions

    async def get_quiz_key(self, session: AsyncSession, quiz_id: UUID) -> list[Question]:
        """Fetch all questions for a quiz WITH correct_answer. Used only by service for grading."""
        stmt = select(Question).where(Question.quiz_id == quiz_id).order_by(Question.id)
        result = await session.execute(stmt)
        return list(result.scalars().all())


crud_quiz = QuizCRUD()
