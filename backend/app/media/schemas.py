import uuid
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Kind = Literal["image", "audio", "video"]


class MediaOut(BaseModel):
    id: uuid.UUID
    kind: Kind
    source: Literal["link", "upload", "youtube"]
    url: str  # adres do wyswietlenia (link albo /api/media/...)
    youtubeId: str | None = None
    startS: int | None = None
    endS: int | None = None
    mime: str | None = None


# media z linku: obraz, dzwiek, wideo albo film z YouTube (wtedy kind = video)
class MediaLinkIn(BaseModel):
    kind: Kind
    url: str = Field(min_length=8, max_length=2000)
    startS: int | None = Field(default=None, ge=0, le=86400)
    endS: int | None = Field(default=None, ge=1, le=86400)

    @model_validator(mode="after")
    def checkRange(self):
        if self.startS is not None and self.endS is not None and self.endS <= self.startS:
            raise ValueError("endS musi byc wiekszy niz startS")
        return self
