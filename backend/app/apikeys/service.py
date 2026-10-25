import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.common.crypto import decrypt, encrypt
from app.config import getSettings
from app.security.models import ApiKey


def keyOut(k: ApiKey) -> dict:
    return {
        "id": k.id,
        "provider": k.provider,
        "label": k.label,
        "last4": k.last4,
        "createdAt": k.createdAt,
        "lastUsedAt": k.lastUsedAt,
    }


# zapisuje zaszyfrowany klucz; id uzytkownika jest czescia szyfrowania (klucz nie da sie przeniesc)
def newKey(user: User, provider: str, label: str, raw: str) -> ApiKey:
    ver, nonce, data = encrypt(raw, user.id.bytes)
    return ApiKey(
        userId=user.id,
        provider=provider,
        label=label.strip() or provider,
        ciphertext=data,
        nonce=nonce,
        keyVersion=ver,
        last4=raw[-4:],
    )


async def listKeys(db: AsyncSession, user: User) -> list[ApiKey]:
    rows = await db.scalars(select(ApiKey).where(ApiKey.userId == user.id).order_by(ApiKey.createdAt))
    return list(rows.all())


def systemKey(provider: str) -> str:
    s = getSettings()
    if not s.allowSystemKeys:
        return ""
    return {
        "openrouter": s.openrouterApiKey,
        "openai": s.openaiApiKey,
        "anthropic": s.anthropicApiKey,
        "google": s.googleApiKey,
    }.get(provider, "")


# klucz do uzycia przy generowaniu (etap 4): najpierw wlasny uzytkownika, potem systemowy.
# Odszyfrowanie tylko tutaj, w miejscu uzycia; klucz nie trafia do odpowiedzi ani logow.
async def keyForUse(db: AsyncSession, userId: uuid.UUID, provider: str) -> tuple[str, str] | None:
    k = await db.scalar(
        select(ApiKey)
        .where(ApiKey.userId == userId, ApiKey.provider == provider)
        .order_by(ApiKey.createdAt.desc())
    )
    if k:
        k.lastUsedAt = datetime.now(UTC)
        await db.commit()
        return decrypt(k.keyVersion, k.nonce, k.ciphertext, userId.bytes), "user"
    sys = systemKey(provider)
    return (sys, "system") if sys else None
