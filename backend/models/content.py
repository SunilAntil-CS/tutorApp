"""Content layer entities: Tenant, User, Book, Chapter, Lesson, Quiz, Question, LessonProgress, Concept, LearningEvent (SQLModel with UUID PKs where applicable)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


# ---------------------------------------------------------------------------
# Tenant & User (Multi-Tenant SaaS)
# ---------------------------------------------------------------------------


class Tenant(SQLModel, table=True):
    """Tenant (school/organization) for multi-tenant isolation."""

    __tablename__ = "tenants"  # type: ignore[assignment]

    id: str = Field(primary_key=True, max_length=64)
    name: str
    domain: str | None = None
    config_json: str = Field(default="{}", sa_column=Column(Text, nullable=False, server_default="'{}'"))


class User(SQLModel, table=True):
    """User belonging to a tenant. Same email can exist in different tenants."""

    __tablename__ = "users"  # type: ignore[assignment]
    __table_args__ = (UniqueConstraint("email", "tenant_id", name="uq_user_email_per_tenant"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    email: str
    hashed_password: str | None = None
    is_active: bool = True


# ---------------------------------------------------------------------------
# Content (tenant-scoped)
# ---------------------------------------------------------------------------


class Book(SQLModel, table=True):
    """Book (e.g. Science Class 10)."""

    __tablename__ = "books"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    title: str
    grade: int = Field(ge=6, le=10)
    subject: str
    cover_image: str | None = None
    updated_at: datetime | None = None  # Set by app when book is updated (optional for now)


class Chapter(SQLModel, table=True):
    """Chapter (e.g. Chemical Reactions) belonging to a Book."""

    __tablename__ = "chapters"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    book_id: UUID = Field(foreign_key="books.id")
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    sequence_number: int
    title: str


class Lesson(SQLModel, table=True):
    """Lesson: either in a Chapter (chapter_id set) or standalone Quick Note (chapter_id None)."""

    __tablename__ = "lessons"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chapter_id: UUID | None = Field(default=None, foreign_key="chapters.id")
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
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

    __tablename__ = "quizzes"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lesson_id: UUID = Field(foreign_key="lessons.id")
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    title: str = "Quiz"

    lesson: Lesson = Relationship(back_populates="quiz")
    questions: list["Question"] = Relationship(back_populates="quiz")


class Question(SQLModel, table=True):
    """MCQ question (Many-to-One with Quiz). correct_answer is A/B/C/D."""

    __tablename__ = "questions"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quiz_id: UUID = Field(foreign_key="quizzes.id")
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str = Field(max_length=1)  # 'A' | 'B' | 'C' | 'D'

    quiz: Quiz = Relationship(back_populates="questions")


class LessonProgress(SQLModel, table=True):
    """User progress on a lesson (completed, quiz score). One row per user per lesson."""

    __tablename__ = "lesson_progress"  # type: ignore[assignment]
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    user_id: UUID = Field(foreign_key="users.id")
    lesson_id: UUID = Field(foreign_key="lessons.id")
    is_completed: bool = False
    quiz_score: int | None = None  # 0–100


# ---------------------------------------------------------------------------
# SaaS prep: Concept & LearningEvent
# ---------------------------------------------------------------------------


class Concept(SQLModel, table=True):
    """Learning concept/topic (tenant-scoped). Used for tagging and analytics."""

    __tablename__ = "concepts"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    name: str
    description: str | None = None


class LearningEvent(SQLModel, table=True):
    """Audit/analytics event (e.g. lesson started, quiz completed)."""

    __tablename__ = "learning_events"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    lesson_id: UUID | None = Field(default=None, foreign_key="lessons.id")
    event_type: str  # e.g. 'lesson_started', 'quiz_completed'
    payload_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
