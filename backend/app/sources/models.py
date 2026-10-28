import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# material uzytkownika: plik albo strona WWW, z wyciagnietym tekstem
class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ownerId: Mapped[uuid.UUID] = mapped_column(
        "owner_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(8))  # file / url
    name: Mapped[str] = mapped_column(String(300))
    mime: Mapped[str] = mapped_column(String(100), default="", server_default="")
    extractedText: Mapped[str] = mapped_column("extracted_text", Text)
    tokenCount: Mapped[int] = mapped_column("token_count", Integer)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )


# fragment materialu (ok. 800 tokenow) z opcjonalnym embeddingiem
class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    documentId: Mapped[uuid.UUID] = mapped_column(
        "document_id", ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    idx: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    tokenCount: Mapped[int] = mapped_column("token_count", Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector())
