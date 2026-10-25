import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apikeys import providers, service
from app.apikeys.schemas import ApiKeyIn, ApiKeyOut, AuditOut
from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.auth.sessions import COOKIE
from app.db.redis import getRedis
from app.db.session import getDb
from app.security.audit import audit
from app.security.models import ApiKey, AuditLog
from app.twofactor.service import hasStepUp

router = APIRouter(prefix="/me", tags=["api-keys"])


# klucze wymagaja 2FA i swiezego potwierdzenia kodem (step-up, 5 min)
async def requireStepUp(
    request: Request, user: User = Depends(getCurrentUser), redis: Redis = Depends(getRedis)
) -> User:
    if not user.totpEnabledAt:
        raise HTTPException(403, "2fa_required")
    if not await hasStepUp(redis, request.cookies.get(COOKIE)):
        raise HTTPException(403, "step_up_required")
    return user


@router.get("/api-keys")
async def listKeys(
    user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> list[ApiKeyOut]:
    return [ApiKeyOut(**service.keyOut(k)) for k in await service.listKeys(db, user)]


# dodaje klucz po sprawdzeniu go u dostawcy
@router.post("/api-keys", status_code=201)
async def addKey(
    data: ApiKeyIn,
    request: Request,
    user: User = Depends(requireStepUp),
    db: AsyncSession = Depends(getDb),
) -> ApiKeyOut:
    raw = data.key.strip()
    await providers.testKey(data.provider, raw)
    k = service.newKey(user, data.provider, data.label, raw)
    db.add(k)
    audit(db, request, user, "api_key_added", f"{data.provider} ...{k.last4}")
    await db.commit()
    await db.refresh(k)
    return ApiKeyOut(**service.keyOut(k))


@router.delete("/api-keys/{keyId}", status_code=204)
async def deleteKey(
    keyId: uuid.UUID,
    request: Request,
    user: User = Depends(requireStepUp),
    db: AsyncSession = Depends(getDb),
) -> None:
    k = await db.get(ApiKey, keyId)
    if not k or k.userId != user.id:
        raise HTTPException(404, "api_key_not_found")
    audit(db, request, user, "api_key_deleted", f"{k.provider} ...{k.last4}")
    await db.delete(k)
    await db.commit()


# ostatnie zdarzenia bezpieczenstwa uzytkownika
@router.get("/audit")
async def auditLog(user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)) -> list[AuditOut]:
    rows = await db.scalars(
        select(AuditLog).where(AuditLog.userId == user.id).order_by(AuditLog.createdAt.desc()).limit(30)
    )
    return [AuditOut(action=a.action, detail=a.detail, ip=a.ip, createdAt=a.createdAt) for a in rows]
