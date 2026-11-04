import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.media.schemas import MediaOut


class StartIn(BaseModel):
    quizId: uuid.UUID
    token: str | None = Field(default=None, max_length=32)  # quiz "tylko z linkiem"


# rozklad pytan: boxes[0] = niewidziane, boxes[1..5] = pudelka Leitnera
class Stats(BaseModel):
    total: int
    boxes: list[int]
    mastered: int
    masteredPct: int


class SessionOut(BaseModel):
    id: uuid.UUID
    quizId: uuid.UUID
    quizTitle: str
    startedAt: datetime
    endedAt: datetime | None
    answered: int
    correct: int
    stats: Stats


# pytanie dla ucznia: bez poprawnych odpowiedzi (sprawdza serwer)
class PlayOption(BaseModel):
    id: uuid.UUID
    text: str


class PlayQuestion(BaseModel):
    id: uuid.UUID
    type: str
    text: str
    media: MediaOut | None
    options: list[PlayOption]
    box: int | None  # None = pierwszy raz


class NextOut(BaseModel):
    question: PlayQuestion | None
    stats: Stats


class AnswerIn(BaseModel):
    questionId: uuid.UUID
    optionIds: list[uuid.UUID] = Field(default_factory=list, max_length=10)
    odp: str = Field(default="", max_length=200)


# informacja zwrotna: poprawna odpowiedz, wyjasnienie i cytat ze zrodla
class AnswerOut(BaseModel):
    correct: bool
    correctOptionIds: list[uuid.UUID]
    accepted: list[str]
    explanation: str
    sourceQuote: str | None
    prevBox: int | None
    box: int
    answered: int
    correctCount: int
    stats: Stats
