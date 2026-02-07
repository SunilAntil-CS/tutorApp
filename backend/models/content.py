"""Content layer entities: Book, Chapter, Lesson, Quiz, Question, LessonProgress (SQLModel with UUID PKs)."""

from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Book(SQLModel, table=True):
    """Book (e.g. Science Class 10)."""

    __tablename__ = "books"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    grade: int = Field(ge=6, le=10)
    subject: str
    cover_image: str | None = None


class Chapter(SQLModel, table=True):
    """Chapter (e.g. Chemical Reactions) belonging to a Book."""

    __tablename__ = "chapters"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    book_id: UUID = Field(foreign_key="books.id")
    sequence_number: int
    title: str


class Lesson(SQLModel, table=True):
    """Lesson: either in a Chapter (chapter_id set) or standalone Quick Note (chapter_id None)."""

    __tablename__ = "lessons"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chapter_id: UUID | None = Field(default=None, foreign_key="chapters.id")
    title: str
    subject: str | None = None  # For standalone lessons (no Book to inherit from)
    is_quick_note: bool = False
    video_id: str | None = Field(default=None)  # None = PDF-only lesson
    pdf_url: str | None = None
    duration_seconds: int | None = None
    is_free: bool = True

    quiz: "Quiz" = Relationship(back_populates="lesson")


class Quiz(SQLModel, table=True):
    """Quiz (One-to-One with Lesson). MCQ questions in separate Question table."""

    __tablename__ = "quizzes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lesson_id: UUID = Field(foreign_key="lessons.id")
    title: str = "Quiz"

    lesson: Lesson = Relationship(back_populates="quiz")
    questions: list["Question"] = Relationship(back_populates="quiz")


class Question(SQLModel, table=True):
    """MCQ question (Many-to-One with Quiz). correct_answer is A/B/C/D."""

    __tablename__ = "questions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quiz_id: UUID = Field(foreign_key="quizzes.id")
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str = Field(max_length=1)  # 'A' | 'B' | 'C' | 'D'

    quiz: Quiz = Relationship(back_populates="questions")


class LessonProgress(SQLModel, table=True):
    """User progress on a lesson (completed, quiz score). One row per user per lesson."""

    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID  # FK to User when auth module exists
    lesson_id: UUID = Field(foreign_key="lessons.id")
    is_completed: bool = False
    quiz_score: int | None = None  # 0–100
