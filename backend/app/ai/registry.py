from functools import lru_cache
from pathlib import Path

import httpx
import yaml
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apikeys.service import systemKey
from app.auth.models import User
from app.config import getSettings
from app.security.models import ApiKey


class ModelOut(BaseModel):
    provider: str
    id: str
    name: str
    context: int | None
    priceIn: float | None
    priceOut: float | None
    source: str  # user (wlasny klucz) / system (klucz z .env) / local (LM Studio)


@lru_cache
def registry() -> list[dict]:
    path = Path(__file__).with_name("models.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))["models"]


# modele z LM Studio (serwer zgodny z API OpenAI); brak serwera = pusta lista
async def localModels() -> list[ModelOut]:
    url = getSettings().lmstudioBaseUrl.rstrip("/") + "/models"
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            data = (await client.get(url)).json()
    except (httpx.HTTPError, ValueError):
        return []
    return [
        ModelOut(
            provider="lmstudio",
            id=m["id"],
            name=m["id"],
            context=None,
            priceIn=None,
            priceOut=None,
            source="local",
        )
        for m in data.get("data", [])
        if "embed" not in m["id"].lower()
    ]


# modele dostepne dla uzytkownika: z jego kluczy, z kluczy systemowych i lokalne
async def availableModels(db: AsyncSession, user: User) -> list[ModelOut]:
    own = set(await db.scalars(select(ApiKey.provider).where(ApiKey.userId == user.id)))
    out = []
    for m in registry():
        source = "user" if m["provider"] in own else "system" if systemKey(m["provider"]) else None
        if source:
            out.append(ModelOut(**m, source=source))
    return out + await localModels()
