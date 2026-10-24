import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.media.models import Media


# quiz: ustawienia i lista pytan
class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ownerId: Mapped[uuid.UUID] = mapped_column(
        "owner_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(1000), default="", server_default="")
    language: Mapped[str] = mapped_column(String(2), default="pl", server_default="pl")
    # public / unlisted (tylko z linkiem) / friends / private
    visibility: Mapped[str] = mapped_column(String(10), default="private", server_default="private")
    shareToken: Mapped[str] = mapped_column("share_token", String(32), unique=True)
    coverMediaId: Mapped[uuid.UUID | None] = mapped_column(
        "cover_media_id", ForeignKey("media.id", ondelete="SET NULL")
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(30)), default=list, server_default="{}")
    originQuizId: Mapped[uuid.UUID | None] = mapped_column(
        "origin_quiz_id", ForeignKey("quizzes.id", ondelete="SET NULL")
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), server_default=func.now()
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="quiz",
        order_by="Question.position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cover: Mapped[Media | None] = relationship(lazy="selectin")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    quizId: Mapped[uuid.UUID] = mapped_column(
        "quiz_id", ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(12))  # single / multi / true_false / open
    text: Mapped[str] = mapped_column(String(500))
    explanation: Mapped[str] = mapped_column(String(1000), default="", server_default="")
    difficulty: Mapped[int] = mapped_column(SmallInteger, default=2, server_default="2")
    timeLimitS: Mapped[int | None] = mapped_column("time_limit_s", Integer)
    points: Mapped[int | None] = mapped_column(Integer)
    mediaId: Mapped[uuid.UUID | None] = mapped_column("media_id", ForeignKey("media.id", ondelete="SET NULL"))
    category: Mapped[str | None] = mapped_column(String(50))  # kategoria w Jeopardy
    origin: Mapped[str] = mapped_column(String(8), default="manual", server_default="manual")
    # pola uzupelniane przy generowaniu przez AI (etap 4)
    generationJobId: Mapped[uuid.UUID | None] = mapped_column("generation_job_id")
    sourceChunkId: Mapped[uuid.UUID | None] = mapped_column("source_chunk_id")
    sourceQuote: Mapped[str | None] = mapped_column("source_quote", Text)

    quiz: Mapped[Quiz] = relationship(back_populates="questions")
    options: Mapped[list["AnswerOption"]] = relationship(
        order_by="AnswerOption.position", cascade="all, delete-orphan", lazy="selectin"
    )
    openAnswer: Mapped["OpenAnswer | None"] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )
    media: Mapped[Media | None] = relationship(lazy="selectin")


# odpowiedz do wyboru (ABCD, wielokrotny wybor, prawda/falsz)
class AnswerOption(Base):
    __tablename__ = "answer_options"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    questionId: Mapped[uuid.UUID] = mapped_column(
        "question_id", ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(200))
    isCorrect: Mapped[bool] = mapped_column("is_correct", Boolean, default=False)


# zasady sprawdzania pytania otwartego
class OpenAnswer(Base):
    __tablename__ = "open_answers"

    questionId: Mapped[uuid.UUID] = mapped_column(
        "question_id", ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    accepted: Mapped[list[str]] = mapped_column(ARRAY(String(200)))
    fuzzyThreshold: Mapped[int] = mapped_column("fuzzy_threshold", SmallInteger, default=85)
    caseSensitive: Mapped[bool] = mapped_column("case_sensitive", Boolean, default=False)
    ignoreAccents: Mapped[bool] = mapped_column("ignore_accents", Boolean, default=True)
