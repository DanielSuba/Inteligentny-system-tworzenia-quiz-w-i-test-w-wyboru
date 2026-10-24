import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# publiczna czesc konta: nazwa, avatar, ustawienia wygladu
class Profile(Base):
    __tablename__ = "profiles"

    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    username: Mapped[str] = mapped_column(String(24), unique=True)
    displayName: Mapped[str] = mapped_column("display_name", String(50))
    avatarPath: Mapped[str | None] = mapped_column("avatar_path", String(255))
    bio: Mapped[str] = mapped_column(String(300), default="", server_default="")
    locale: Mapped[str] = mapped_column(String(2), default="pl", server_default="pl")
    palette: Mapped[str] = mapped_column(String(16), default="grafit", server_default="grafit")
