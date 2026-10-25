import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Provider = Literal["openrouter", "openai", "anthropic", "google"]


class ApiKeyIn(BaseModel):
    provider: Provider
    label: str = Field(default="", max_length=50)
    key: str = Field(min_length=10, max_length=300)


# klucz na liscie: sam klucz nigdy nie wraca, tylko 4 ostatnie znaki
class ApiKeyOut(BaseModel):
    id: uuid.UUID
    provider: Provider
    label: str
    last4: str
    createdAt: datetime
    lastUsedAt: datetime | None


class AuditOut(BaseModel):
    action: str
    detail: str
    ip: str
    createdAt: datetime
