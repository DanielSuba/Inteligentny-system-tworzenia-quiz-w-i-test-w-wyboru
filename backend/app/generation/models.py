import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# jedno generowanie: wszystko, co potrzebne do badan (model, strategia, prompt, koszty, czas)
class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    quizId: Mapped[uuid.UUID] = mapped_column(
        "quiz_id", ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    sourceMode: Mapped[str] = mapped_column("source_mode", String(8))  # material / topic
    strategy: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(16))
    model: Mapped[str] = mapped_column(String(120))
    actualProvider: Mapped[str | None] = mapped_column("actual_provider", String(60))
    keySource: Mapped[str] = mapped_column("key_source", String(8))  # user / system / local
    promptVersion: Mapped[str] = mapped_column("prompt_version", String(40))
    params: Mapped[dict] = mapped_column(JSONB)
    documentIds: Mapped[list[uuid.UUID]] = mapped_column("document_ids", ARRAY(Uuid), default=list)
    status: Mapped[str] = mapped_column(String(10), default="queued")  # queued/running/done/error
    progress: Mapped[int] = mapped_column(Integer, default=0)
    calls: Mapped[int] = mapped_column(Integer, default=0)
    tokensIn: Mapped[int] = mapped_column("tokens_in", Integer, default=0)
    tokensOut: Mapped[int] = mapped_column("tokens_out", Integer, default=0)
    costUsd: Mapped[float | None] = mapped_column("cost_usd", Float)
    durationMs: Mapped[int] = mapped_column("duration_ms", Integer, default=0)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )
    finishedAt: Mapped[datetime | None] = mapped_column("finished_at", DateTime(timezone=True))


# pytanie zwrocone przez model, z wynikami automatycznych sprawdzen
class GeneratedQuestion(Base):
    __tablename__ = "generated_questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    jobId: Mapped[uuid.UUID] = mapped_column(
        "job_id", ForeignKey("generation_jobs.id", ondelete="CASCADE"), index=True
    )
    idx: Mapped[int] = mapped_column(Integer)
    chunkId: Mapped[uuid.UUID | None] = mapped_column(
        "chunk_id", ForeignKey("source_chunks.id", ondelete="SET NULL")
    )
    rawOutput: Mapped[dict] = mapped_column("raw_output", JSONB)
    parsed: Mapped[dict] = mapped_column(JSONB)
    grounded: Mapped[bool | None] = mapped_column(Boolean)
    groundingScore: Mapped[float | None] = mapped_column("grounding_score", Float)
    duplicateOf: Mapped[str | None] = mapped_column("duplicate_of", String(500))
    validationErrors: Mapped[list] = mapped_column("validation_errors", JSONB, default=list)
    status: Mapped[str] = mapped_column(
        String(10), default="pending"
    )  # pending/accepted/edited/rejected/replaced
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )


# decyzja recenzenta (dane do badan: ile pytan przyjeto bez zmian, jak duze byly poprawki)
class QuestionReview(Base):
    __tablename__ = "question_reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    generatedQuestionId: Mapped[uuid.UUID] = mapped_column(
        "generated_question_id", ForeignKey("generated_questions.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(10))  # accepted / edited / rejected
    final: Mapped[dict | None] = mapped_column(JSONB)
    editDistance: Mapped[int] = mapped_column("edit_distance", Integer, default=0)
    questionId: Mapped[uuid.UUID | None] = mapped_column(
        "question_id", ForeignKey("questions.id", ondelete="SET NULL")
    )
    reviewedAt: Mapped[datetime] = mapped_column(
        "reviewed_at", DateTime(timezone=True), server_default=func.now()
    )
