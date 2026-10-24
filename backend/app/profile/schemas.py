import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.auth.schemas import Locale, Password

Palette = Literal["grafit", "mosiadz", "rubin"]


# dane zalogowanego uzytkownika wysylane do frontendu
class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    emailVerified: bool
    role: str
    username: str
    displayName: str
    avatarUrl: str | None
    bio: str
    locale: Locale
    palette: Palette


class MeUpdate(BaseModel):
    username: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_]{3,24}$")
    displayName: str | None = Field(default=None, min_length=1, max_length=50)
    bio: str | None = Field(default=None, max_length=300)
    locale: Locale | None = None
    palette: Palette | None = None


class PasswordChangeIn(BaseModel):
    currentPassword: str = Field(max_length=128)
    newPassword: str = Password
