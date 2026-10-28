import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

QType = Literal["single", "multi", "true_false", "open"]
Bloom = Literal["remember", "understand", "apply", "analyze", "evaluate", "create"]

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@ Odpowiedz modelu (schemat) @@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# schemat celowo luzny: zasady typow pytan sprawdzamy osobno i zapisujemy jako bledy walidacji


class GenOption(BaseModel):
    text: str
    isCorrect: bool


class GenQuestion(BaseModel):
    question: str = Field(description="Tresc pytania")
    type: QType
    options: list[GenOption] = Field(default_factory=list, description="Puste dla type=open")
    acceptedAnswers: list[str] = Field(default_factory=list, description="Tylko dla type=open")
    explanation: str = Field(default="", description="Krotkie wyjasnienie poprawnej odpowiedzi")
    sourceQuote: str = Field(
        default="", description="Doslowny cytat z materialu, na ktorym opiera sie pytanie"
    )
    difficulty: int = Field(default=2, ge=1, le=3)
    bloomLevel: Bloom = "remember"
    topic: str = ""


class GenBatch(BaseModel):
    questions: list[GenQuestion]


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$ API $$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


class JobIn(BaseModel):
    quizId: uuid.UUID
    provider: Literal["openrouter", "openai", "anthropic", "google", "lmstudio"]
    model: str = Field(min_length=1, max_length=120)
    strategy: Literal["few_shot", "zero_shot"] = "few_shot"
    mode: Literal["material", "topic"]
    documentIds: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    topic: str = Field(default="", max_length=300)  # tryb "z tematu"
    focus: str = Field(default="", max_length=300)  # tematy przewodnie w trybie "z materialu"
    count: int = Field(default=10, ge=1, le=50)
    types: list[QType] = Field(default_factory=lambda: ["single"], min_length=1)
    difficulty: int = Field(default=0, ge=0, le=3)  # 0 = mieszana
    language: Literal["pl", "en"] = "pl"
    temperature: float = Field(default=0.7, ge=0, le=1.5)

    @model_validator(mode="after")
    def checkSource(self):
        if self.mode == "material" and not self.documentIds:
            raise ValueError("tryb z materialu wymaga co najmniej jednego materialu")
        if self.mode == "topic" and not self.topic.strip():
            raise ValueError("tryb z tematu wymaga tematu")
        return self


class EstimateOut(BaseModel):
    tokensIn: int
    tokensOut: int
    costUsd: float | None


class GenQuestionOut(BaseModel):
    id: uuid.UUID
    idx: int
    parsed: dict
    chunkText: str | None
    grounded: bool | None
    groundingScore: float | None
    duplicateOf: str | None
    validationErrors: list
    status: str


class JobOut(BaseModel):
    id: uuid.UUID
    quizId: uuid.UUID
    sourceMode: str
    strategy: str
    provider: str
    model: str
    keySource: str
    promptVersion: str
    params: dict
    status: str
    progress: int
    calls: int
    tokensIn: int
    tokensOut: int
    costUsd: float | None
    durationMs: int
    retries: int
    error: str | None
    createdAt: datetime
    questions: list[GenQuestionOut] = []
