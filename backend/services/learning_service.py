"""Business logic for syllabus and content: books, structure, lesson detail, quiz. No HTTP; pure Python."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_content import crud_content
from logging_config import get_logger

log = get_logger("learning_service")
from crud.crud_quiz import crud_quiz
from schemas.content_schema import (
    BookResponse,
    BookStructureResponse,
    ChapterStructureItem,
    LessonDetailResponse,
    LessonRead,
    LessonStructureItem,
    QuestionPublic,
    QuizDetail,
    QuizRead,
    QuizResult,
    QuizSubmission,
)
from models.content import Book, Chapter, Lesson, Question, Quiz


def _book_to_response(book: Book) -> BookResponse:
    return BookResponse(
        id=book.id,
        title=book.title,
        grade=book.grade,
        subject=book.subject,
        cover_image=book.cover_image,
    )


def _lesson_to_structure_item(lesson: Lesson) -> LessonStructureItem:
    return LessonStructureItem(
        id=lesson.id,
        title=lesson.title,
        is_free=lesson.is_free,
        duration=lesson.duration_seconds,
    )


def _chapter_to_structure_item(chapter: Chapter, lessons: list[Lesson]) -> ChapterStructureItem:
    return ChapterStructureItem(
        id=chapter.id,
        title=chapter.title,
        sequence=chapter.sequence_number,
        lessons=[_lesson_to_structure_item(l) for l in lessons],
    )


def _question_to_public(q: Question) -> QuestionPublic:
    """Exclude correct_answer (anti-cheating)."""
    return QuestionPublic(
        id=q.id,
        text=q.text,
        option_a=q.option_a,
        option_b=q.option_b,
        option_c=q.option_c,
        option_d=q.option_d,
    )


def _quiz_to_detail(quiz: Quiz, questions: list[Question]) -> QuizDetail:
    return QuizDetail(
        id=quiz.id,
        title=quiz.title,
        questions=[_question_to_public(q) for q in questions],
    )


def _lesson_to_read(lesson: Lesson) -> LessonRead:
    return LessonRead(
        id=lesson.id,
        title=lesson.title,
        chapter_id=lesson.chapter_id,
        subject=lesson.subject,
        is_quick_note=lesson.is_quick_note,
        video_id=lesson.video_id,
        pdf_url=lesson.pdf_url,
        duration_seconds=lesson.duration_seconds,
        is_free=lesson.is_free,
    )


async def get_all_books(session: AsyncSession) -> list[BookResponse]:
    """Return all books as API DTOs."""
    books = await crud_content.get_books(session)
    log.info("DB: get_all_books -> %d books", len(books))
    return [_book_to_response(b) for b in books]


async def get_book_structure(session: AsyncSession, book_id: UUID) -> BookStructureResponse | None:
    """Return book syllabus tree (chapters with lessons) for GET /books/{book_id}/structure."""
    book = await crud_content.get_book_by_id(session, book_id)
    if not book:
        log.info("DB: get_book_structure(book_id=%s) -> not found", book_id)
        return None
    chapters = await crud_content.get_chapters_by_book_id(session, book_id)
    chapter_dtos = []
    for ch in chapters:
        lessons = await crud_content.get_lessons_by_chapter_id(session, ch.id)
        chapter_dtos.append(_chapter_to_structure_item(ch, lessons))
    log.info("DB: get_book_structure(book_id=%s) -> %d chapters", book_id, len(chapter_dtos))
    return BookStructureResponse(book_id=book_id, chapters=chapter_dtos)


async def get_lesson_detail(session: AsyncSession, lesson_id: UUID) -> LessonDetailResponse | None:
    """Return lesson + quiz for GET /lessons/{lesson_id} (player view)."""
    lesson = await crud_content.get_lesson_by_id(session, lesson_id)
    if not lesson:
        log.info("DB: get_lesson_detail(lesson_id=%s) -> not found", lesson_id)
        return None
    quiz, questions = await crud_quiz.get_quiz_for_lesson(session, lesson_id)
    log.info("DB: get_lesson_detail(lesson_id=%s) -> lesson + %d quiz questions", lesson_id, len(questions) if questions else 0)
    return LessonDetailResponse(
        id=lesson.id,
        title=lesson.title,
        chapter_id=lesson.chapter_id,
        subject=lesson.subject,
        is_quick_note=lesson.is_quick_note,
        video_id=lesson.video_id,
        pdf_url=lesson.pdf_url,
        quiz=_quiz_to_detail(quiz, questions) if quiz else None,
    )


async def get_quick_notes(
    session: AsyncSession, subject: str | None = None
) -> list[LessonRead]:
    """Return standalone Quick Concept lessons, optionally filtered by subject."""
    lessons = await crud_content.get_quick_notes(session, subject=subject)
    log.info("DB: get_quick_notes(subject=%s) -> %d lessons", subject, len(lessons))
    return [_lesson_to_read(l) for l in lessons]


async def get_quiz_read(session: AsyncSession, lesson_id: UUID) -> QuizRead | None:
    """Return quiz for GET /lessons/{id}/quiz (title + questions without correct_answer)."""
    quiz, questions = await crud_quiz.get_quiz_for_lesson(session, lesson_id)
    if not quiz:
        log.info("DB: get_quiz_read(lesson_id=%s) -> not found", lesson_id)
        return None
    log.info("DB: get_quiz_read(lesson_id=%s) -> %d questions", lesson_id, len(questions) if questions else 0)
    return QuizRead(
        title=quiz.title,
        questions=[_question_to_public(q) for q in questions],
    )


async def submit_quiz_attempt(
    session: AsyncSession,
    user_id: UUID,
    lesson_id: UUID,
    submission: QuizSubmission,
) -> QuizResult:
    """
    Grade submission, update LessonProgress if passed (>70%), return result.
    """
    quiz, _ = await crud_quiz.get_quiz_for_lesson(session, lesson_id)
    if not quiz:
        raise ValueError("No quiz for this lesson")
    key = await crud_quiz.get_quiz_key(session, quiz.id)
    correct_map = {q.id: q.correct_answer for q in key}
    total = len(correct_map)
    if total == 0:
        score_percentage = 0.0
    else:
        correct = sum(
            1 for a in submission.answers
            if correct_map.get(a.question_id) == a.selected_option
        )
        score_percentage = (correct / total) * 100.0
    passed = score_percentage > 70
    if passed:
        await crud_content.upsert_lesson_progress(
            session,
            user_id=user_id,
            lesson_id=lesson_id,
            is_completed=True,
            quiz_score=round(score_percentage),
        )
    mastery_badge = "gold" if score_percentage >= 90 else ("silver" if passed else None)
    log.info("DB: submit_quiz_attempt(lesson_id=%s) -> %.1f%% passed=%s", lesson_id, score_percentage, passed)
    return QuizResult(
        score_percentage=round(score_percentage, 1),
        passed=passed,
        mastery_badge=mastery_badge,
    )
