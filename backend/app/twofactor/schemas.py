from pydantic import BaseModel, Field


class CodeIn(BaseModel):
    code: str = Field(min_length=6, max_length=20)


class StatusOut(BaseModel):
    enabled: bool
    backupCodesLeft: int
    stepUpActive: bool


class SetupOut(BaseModel):
    secret: str  # do recznego wpisania, gdy nie da sie zeskanowac QR
    uri: str
    qr: str  # obraz SVG jako data URI


class CodesOut(BaseModel):
    codes: list[str]
