import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, SmallInteger, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# postep ucznia w jednym pytaniu (system Leitnera: pudelka 1-5)
class LearningProgress(Base):
    __tablename__ = "learning_progress"

    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    questionId: Mapped[uuid.UUID] = mapped_column(
        "question_id", ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    box: Mapped[int] = mapped_column(SmallInteger, default=1)
    correctCount: Mapped[int] = mapped_column("correct_count", Integer, default=0)
    wrongCount: Mapped[int] = mapped_column("wrong_count", Integer, default=0)
    lastSeenAt: Mapped[datetime] = mapped_column("last_seen_at", DateTime(timezone=True))
    lastResult: Mapped[bool] = mapped_column("last_result", Boolean)


# jedna sesja nauki (statystyki + pytanie, na ktore czekamy)
class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    quizId: Mapped[uuid.UUID] = mapped_column(
        "quiz_id", ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    startedAt: Mapped[datetime] = mapped_column(
        "started_at", DateTime(timezone=True), server_default=func.now()
    )
    endedAt: Mapped[datetime | None] = mapped_column("ended_at", DateTime(timezone=True))
    answered: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    # pytanie pokazane i jeszcze bez odpowiedzi
    currentId: Mapped[uuid.UUID | None] = mapped_column("current_question_id", Uuid)
    # ostatnio pokazane pytania (bez powtorek w krotkim oknie)
    recent: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(Uuid), default=list)
