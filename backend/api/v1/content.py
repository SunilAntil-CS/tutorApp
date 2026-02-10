"""Content API (Controller): GET /books, GET /books/{id}/structure, GET /lessons/{id}, quiz. No SQL; no business logic."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_tenant, get_current_user_id, get_db
from logging_config import get_logger
from schemas.content_schema import (
    BookResponse,
    BookStructureResponse,
    LessonDetailResponse,
    LessonRead,
    QuizRead,
    QuizResult,
    QuizSubmission,
)
from services import learning_service

log = get_logger("api.content")

# Tenant gatekeeper: every route under this router validates tenant (DB + cache).
router = APIRouter(dependencies=[Depends(get_current_tenant)])


@router.get("/books", response_model=list[BookResponse])
async def list_books(db: AsyncSession = Depends(get_db)) -> list[BookResponse]:
    """Get all books."""
    return await learning_service.get_all_books(db)


@router.get("/quick-notes", response_model=list[LessonRead])
async def list_quick_notes(
    subject: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[LessonRead]:
    """Get standalone Quick Concept lessons (notes/videos). Optional filter by subject."""
    data = await learning_service.get_quick_notes(db, subject=subject)
    log.info("GET /quick-notes response JSON: %s", json.dumps([m.model_dump(mode="json") for m in data]))
    return data


@router.get("/books/{book_id}/structure", response_model=BookStructureResponse)
async def get_book_structure(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BookStructureResponse:
    """Get book hierarchy (chapters and lessons) for syllabus/index view."""
    structure = await learning_service.get_book_structure(db, book_id)
    if structure is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return structure


@router.get("/lessons/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson_detail(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> LessonDetailResponse:
    """Get lesson details (player view): title, video_id, pdf_url, quiz."""
    lesson = await learning_service.get_lesson_detail(db, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.get("/lessons/{lesson_id}/quiz", response_model=QuizRead)
async def get_lesson_quiz(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> QuizRead:
    """Get quiz for a lesson (title + questions; no correct answers)."""
    quiz = await learning_service.get_quiz_read(db, lesson_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found for this lesson")
    return quiz


@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResult)
async def submit_lesson_quiz(
    lesson_id: UUID,
    body: QuizSubmission,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> QuizResult:
    """Submit quiz answers; returns score, passed, and optional mastery badge. Requires X-User-Id header."""
    try:
        return await learning_service.submit_quiz_attempt(db, user_id, lesson_id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
