import uuid
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Kind = Literal["image", "audio", "video"]


class MediaOut(BaseModel):
    id: uuid.UUID
    kind: Kind
    source: Literal["link", "upload", "youtube", "soundcloud", "spotify"]
    url: str  # adres do wyswietlenia (link albo /api/media/...)
    youtubeId: str | None = None
    embedId: str | None = None
    startS: int | None = None
    endS: int | None = None
    mime: str | None = None
    crop: "Crop | None" = None
    displayWidth: int | None = None
    hideVideo: bool = False


# kadr obrazu w procentach oryginalu
class Crop(BaseModel):
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    w: float = Field(gt=0, le=100)
    h: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def inside(self):
        if self.x + self.w > 100.01 or self.y + self.h > 100.01:
            raise ValueError("kadr wychodzi poza obraz")
        return self


# zmiana ustawien mediow: fragment muzyki/wideo, kadr i wielkosc obrazu, ukrycie wideo
class MediaUpdate(BaseModel):
    startS: int | None = Field(default=None, ge=0, le=86400)
    endS: int | None = Field(default=None, ge=1, le=86400)
    crop: Crop | None = None
    displayWidth: int | None = Field(default=None, ge=10, le=100)
    hideVideo: bool | None = None

    @model_validator(mode="after")
    def checkRange(self):
        if self.startS is not None and self.endS is not None and self.endS <= self.startS:
            raise ValueError("endS musi byc wiekszy niz startS")
        return self


# media z linku: obraz, dzwiek albo wideo; YouTube, SoundCloud i Spotify rozpoznawane automatycznie
class MediaLinkIn(BaseModel):
    kind: Kind
    url: str = Field(min_length=8, max_length=2000)
    startS: int | None = Field(default=None, ge=0, le=86400)
    endS: int | None = Field(default=None, ge=1, le=86400)
    hideVideo: bool | None = None

    @model_validator(mode="after")
    def checkRange(self):
        if self.startS is not None and self.endS is not None and self.endS <= self.startS:
            raise ValueError("endS musi byc wiekszy niz startS")
        return self


MediaOut.model_rebuild()
