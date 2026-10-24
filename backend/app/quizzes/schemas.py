import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.media.schemas import MediaOut

QType = Literal["single", "multi", "true_false", "open"]
Visibility = Literal["public", "unlisted", "friends", "private"]
Lang = Literal["pl", "en"]

MAX_OPTIONS = 10


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Pytania @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


class OptionIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    isCorrect: bool = False


class QuestionIn(BaseModel):
    type: QType
    text: str = Field(min_length=1, max_length=500)
    explanation: str = Field(default="", max_length=1000)
    difficulty: int = Field(default=2, ge=1, le=3)
    timeLimitS: int | None = Field(default=None, ge=5, le=300)
    points: int | None = Field(default=None, ge=0, le=10000)
    category: str | None = Field(default=None, max_length=50)
    mediaId: uuid.UUID | None = None
    options: list[OptionIn] = Field(default_factory=list, max_length=MAX_OPTIONS)
    accepted: list[str] = Field(default_factory=list, max_length=20)
    fuzzyThreshold: int = Field(default=85, ge=50, le=100)
    caseSensitive: bool = False
    ignoreAccents: bool = True

    # zasady dla kazdego typu pytania
    @model_validator(mode="after")
    def checkType(self):
        opts = self.options
        good = sum(o.isCorrect for o in opts)
        if self.type == "open":
            self.accepted = [a.strip() for a in self.accepted if a.strip()]
            if opts:
                raise ValueError("pytanie otwarte nie ma opcji do wyboru")
            if not self.accepted:
                raise ValueError("pytanie otwarte wymaga co najmniej jednej akceptowanej odpowiedzi")
            if any(len(a) > 200 for a in self.accepted):
                raise ValueError("odpowiedz moze miec najwyzej 200 znakow")
            return self

        if self.accepted:
            raise ValueError("akceptowane odpowiedzi sa tylko dla pytan otwartych")
        texts = [o.text.strip().casefold() for o in opts]
        if len(set(texts)) != len(texts):
            raise ValueError("opcje odpowiedzi musza byc rozne")
        if self.type == "true_false":
            if len(opts) != 2 or good != 1:
                raise ValueError("prawda/falsz: dokladnie 2 opcje i 1 poprawna")
        elif len(opts) < 2:
            raise ValueError("pytanie wyboru wymaga od 2 do 10 opcji")
        elif self.type == "single" and good != 1:
            raise ValueError("jednokrotny wybor: dokladnie 1 poprawna odpowiedz")
        elif self.type == "multi" and good < 1:
            raise ValueError("wielokrotny wybor: co najmniej 1 poprawna odpowiedz")
        return self


class OptionOut(BaseModel):
    id: uuid.UUID
    text: str
    isCorrect: bool


class QuestionOut(BaseModel):
    id: uuid.UUID
    position: int
    type: QType
    text: str
    explanation: str
    difficulty: int
    timeLimitS: int | None
    points: int | None
    category: str | None
    origin: str
    sourceQuote: str | None
    media: MediaOut | None
    options: list[OptionOut]
    accepted: list[str]
    fuzzyThreshold: int
    caseSensitive: bool
    ignoreAccents: bool


class OrderIn(BaseModel):
    ids: list[uuid.UUID]


class CheckIn(BaseModel):
    odp: str = Field(max_length=500)


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$ Quizy $$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


class QuizIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    language: Lang = "pl"
    visibility: Visibility = "private"
    tags: list[str] = Field(default_factory=list, max_length=10)
    coverMediaId: uuid.UUID | None = None

    @model_validator(mode="after")
    def cleanTags(self):
        seen = []
        for t in self.tags:
            t = t.strip().lower()[:30]
            if t and t not in seen:
                seen.append(t)
        self.tags = seen
        return self


class QuizUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    language: Lang | None = None
    visibility: Visibility | None = None
    tags: list[str] | None = Field(default=None, max_length=10)
    coverMediaId: uuid.UUID | None = None


class QuizOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    language: Lang
    visibility: Visibility
    tags: list[str]
    shareToken: str | None  # tylko dla wlasciciela
    cover: MediaOut | None
    isOwner: bool
    authorName: str
    questionCount: int
    createdAt: datetime
    updatedAt: datetime


class QuizDetail(QuizOut):
    questions: list[QuestionOut]
