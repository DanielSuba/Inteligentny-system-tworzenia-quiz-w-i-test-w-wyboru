import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# jednorazowy kod zapasowy 2FA (zapisany jako hash)
class BackupCode(Base):
    __tablename__ = "backup_codes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    codeHash: Mapped[str] = mapped_column("code_hash", String(64))
    usedAt: Mapped[datetime | None] = mapped_column("used_at", DateTime(timezone=True))


# klucz API dostawcy AI; sam klucz tylko zaszyfrowany, do przegladarki idzie tylko last4
class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(16))
    label: Mapped[str] = mapped_column(String(50))
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)
    keyVersion: Mapped[int] = mapped_column("key_version", Integer)
    last4: Mapped[str] = mapped_column(String(4))
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )
    lastUsedAt: Mapped[datetime | None] = mapped_column("last_used_at", DateTime(timezone=True))


# dziennik zdarzen bezpieczenstwa (2FA, klucze)
class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(String(200), default="", server_default="")
    ip: Mapped[str] = mapped_column(String(45), default="", server_default="")
    userAgent: Mapped[str] = mapped_column("user_agent", String(300), default="", server_default="")
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now(), index=True
    )
