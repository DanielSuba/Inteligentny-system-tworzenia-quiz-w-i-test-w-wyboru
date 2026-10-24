import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# dekoracja profilu: ramka, baner, tytul, odznaka (wypelniane w etapie 9)
class CosmeticItem(Base):
    __tablename__ = "cosmetic_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(16))
    key: Mapped[str] = mapped_column(String(64), unique=True)
    data: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    unlockRule: Mapped[dict | None] = mapped_column("unlock_rule", JSONB)


# dekoracje, ktore ma uzytkownik; equippedSlot = gdzie jest zalozona
class UserCosmetic(Base):
    __tablename__ = "user_cosmetics"

    userId: Mapped[uuid.UUID] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    itemId: Mapped[uuid.UUID] = mapped_column(
        "item_id", ForeignKey("cosmetic_items.id", ondelete="CASCADE"), primary_key=True
    )
    equippedSlot: Mapped[str | None] = mapped_column("equipped_slot", String(16))
