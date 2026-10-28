import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# obraz, dzwiek albo wideo: link, plik wgrany przez uzytkownika albo film z YouTube
class Media(Base):
    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ownerId: Mapped[uuid.UUID] = mapped_column(
        "owner_id", ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(8))  # image / audio / video
    source: Mapped[str] = mapped_column(String(10))  # link / upload / youtube / soundcloud / spotify
    url: Mapped[str | None] = mapped_column(String(2000))
    path: Mapped[str | None] = mapped_column(String(255))
    youtubeId: Mapped[str | None] = mapped_column("youtube_id", String(16))
    startS: Mapped[int | None] = mapped_column("start_s", Integer)
    endS: Mapped[int | None] = mapped_column("end_s", Integer)
    embedId: Mapped[str | None] = mapped_column("embed_id", String(80))  # np. "track/<id>" dla Spotify
    mime: Mapped[str | None] = mapped_column(String(64))
    # kadr obrazu w % (x, y, w, h) i szerokosc wyswietlania w %; obraz zostaje bez zmian
    crop: Mapped[dict | None] = mapped_column(JSONB)
    displayWidth: Mapped[int | None] = mapped_column("display_width", Integer)
    # muzyka z serwisu z wideo (YouTube): gracz slyszy dzwiek, nie widzi obrazu ani tytulu
    hideVideo: Mapped[bool] = mapped_column("hide_video", Boolean, default=False, server_default="false")
    sizeBytes: Mapped[int | None] = mapped_column("size_bytes", Integer)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )
