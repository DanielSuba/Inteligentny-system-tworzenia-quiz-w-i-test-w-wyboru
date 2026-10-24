import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# konto uzytkownika (dane do logowania)
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    passwordHash: Mapped[str] = mapped_column("password_hash", String(255))
    emailVerifiedAt: Mapped[datetime | None] = mapped_column("email_verified_at", DateTime(timezone=True))
    role: Mapped[str] = mapped_column(String(16), default="user", server_default="user")
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )


# jednorazowy token z e-maila: weryfikacja adresu albo reset hasla
class EmailToken(Base):
    __tablename__ = "email_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(16))
    tokenHash: Mapped[str] = mapped_column("token_hash", String(64), unique=True)
    expiresAt: Mapped[datetime] = mapped_column("expires_at", DateTime(timezone=True))
    usedAt: Mapped[datetime | None] = mapped_column("used_at", DateTime(timezone=True))
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )
