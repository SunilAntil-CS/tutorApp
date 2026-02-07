"""Content API DTOs (Pydantic response models). Match API Interface Design in ARCHITECTURE.md."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ----- Books -----


class BookResponse(BaseModel):
    """GET /books item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    grade: int
    subject: str
    cover_image: str | None = None


# ----- Book structure (syllabus tree) -----


class LessonStructureItem(BaseModel):
    """Lesson item in GET /books/{book_id}/structure."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    is_free: bool = True
    duration: int | None = None  # duration_seconds, named per API contract


class ChapterStructureItem(BaseModel):
    """Chapter item in GET /books/{book_id}/structure."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    sequence: int  # sequence_number
    lessons: list[LessonStructureItem] = []


class BookStructureResponse(BaseModel):
    """GET /books/{book_id}/structure response."""

    book_id: UUID
    chapters: list[ChapterStructureItem] = []


# ----- Lesson (base + read for quick-notes and creation) -----


class LessonBase(BaseModel):
    """Base fields for lesson create/update. chapter_id optional for standalone quick notes."""

    title: str
    chapter_id: UUID | None = None
    subject: str | None = None
    is_quick_note: bool = False
    video_id: str | None = None
    pdf_url: str | None = None
    duration_seconds: int | None = None
    is_free: bool = True


class LessonRead(BaseModel):
    """Lesson list item (e.g. GET /quick-notes)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    chapter_id: UUID | None = None
    subject: str | None = None
    is_quick_note: bool = False
    video_id: str | None = None
    pdf_url: str | None = None
    duration_seconds: int | None = None
    is_free: bool = True


# ----- Lesson detail (player view) -----


class QuestionPublic(BaseModel):
    """MCQ question without correct_answer (anti-cheating)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class QuizDetail(BaseModel):
    """Quiz block in GET /lessons/{lesson_id}."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str = "Quiz"
    questions: list[QuestionPublic] = []


class LessonDetailResponse(BaseModel):
    """GET /lessons/{lesson_id} response. video_id optional (PDF-only). Works for book lessons and quick notes."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    chapter_id: UUID | None = None
    subject: str | None = None
    is_quick_note: bool = False
    video_id: str | None = None
    pdf_url: str | None = None
    quiz: QuizDetail | None = None


# ----- Quiz (MCQ) -----


class QuizRead(BaseModel):
    """GET /lessons/{id}/quiz response. Title + questions (no correct_answer)."""

    title: str = "Quiz"
    questions: list[QuestionPublic] = []


class QuizSubmissionItem(BaseModel):
    """Single answer: question_id and selected option A/B/C/D."""

    question_id: UUID
    selected_option: str = Field(..., pattern="^[ABCD]$")


class QuizSubmission(BaseModel):
    """POST /lessons/{id}/quiz body: list of answers."""

    answers: list[QuizSubmissionItem] = []


class QuizResult(BaseModel):
    """POST /lessons/{id}/quiz response."""

    score_percentage: float
    passed: bool
    mastery_badge: str | None = None
