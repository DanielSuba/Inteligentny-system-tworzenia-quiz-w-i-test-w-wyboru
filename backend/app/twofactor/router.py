from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.auth.sessions import COOKIE
from app.common.ratelimit import rateLimit
from app.db.redis import getRedis
from app.db.session import getDb
from app.security.audit import audit
from app.security.models import ApiKey, BackupCode
from app.twofactor import service
from app.twofactor.schemas import CodeIn, CodesOut, SetupOut, StatusOut

router = APIRouter(prefix="/me/2fa", tags=["2fa"])

# limit prob wpisania kodu
codeLimit = Depends(rateLimit("2fa-code", 10, 300))


@router.get("")
async def status(
    request: Request,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> StatusOut:
    return StatusOut(
        enabled=user.totpEnabledAt is not None,
        backupCodesLeft=await service.backupLeft(db, user),
        stepUpActive=await service.hasStepUp(redis, request.cookies.get(COOKIE)),
    )


# krok 1: nowy sekret i kod QR
@router.post("/setup")
async def setup(user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)) -> SetupOut:
    if user.totpEnabledAt:
        raise HTTPException(409, "2fa_already_enabled")
    secret = service.newSecret(user)
    await db.commit()
    uri, qr = service.qrFor(user, secret)
    return SetupOut(secret=secret, uri=uri, qr=qr)


# krok 2: potwierdzenie kodem z aplikacji; zwraca kody zapasowe (pokazywane tylko raz)
@router.post("/enable", dependencies=[codeLimit])
async def enable(
    data: CodeIn,
    request: Request,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> CodesOut:
    if user.totpEnabledAt:
        raise HTTPException(409, "2fa_already_enabled")
    if not await service.checkTotp(redis, user, data.code.strip()):
        raise HTTPException(400, "invalid_code")
    user.totpEnabledAt = datetime.now(UTC)
    codes = await service.newBackupCodes(db, user)
    audit(db, request, user, "2fa_enabled")
    await db.commit()
    await service.grantStepUp(redis, request.cookies.get(COOKIE, ""))
    return CodesOut(codes=codes)


# wylaczenie 2FA: wymaga kodu; niemozliwe, dopoki sa zapisane klucze API
@router.post("/disable", dependencies=[codeLimit])
async def disable(
    data: CodeIn,
    request: Request,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> StatusOut:
    if not user.totpEnabledAt:
        raise HTTPException(409, "2fa_not_enabled")
    keys = await db.scalar(select(func.count()).select_from(ApiKey).where(ApiKey.userId == user.id))
    if keys:
        raise HTTPException(409, "keys_require_2fa")
    if not await service.checkCode(db, redis, user, data.code):
        raise HTTPException(400, "invalid_code")
    user.totpEnabledAt = user.totpSecret = user.totpNonce = user.totpKeyVersion = None
    await db.execute(delete(BackupCode).where(BackupCode.userId == user.id))
    audit(db, request, user, "2fa_disabled")
    await db.commit()
    return StatusOut(enabled=False, backupCodesLeft=0, stepUpActive=False)


@router.post("/backup-codes", dependencies=[codeLimit])
async def regenerate(
    data: CodeIn,
    request: Request,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> CodesOut:
    if not user.totpEnabledAt:
        raise HTTPException(409, "2fa_not_enabled")
    if not await service.checkCode(db, redis, user, data.code):
        raise HTTPException(400, "invalid_code")
    codes = await service.newBackupCodes(db, user)
    audit(db, request, user, "backup_codes_regenerated")
    await db.commit()
    return CodesOut(codes=codes)


# step-up: potwierdzenie kodem przed zmiana kluczy API (wazne 5 minut)
@router.post("/verify", dependencies=[codeLimit])
async def verify(
    data: CodeIn,
    request: Request,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> StatusOut:
    if not user.totpEnabledAt:
        raise HTTPException(409, "2fa_not_enabled")
    if not await service.checkCode(db, redis, user, data.code):
        audit(db, request, user, "step_up_failed")
        await db.commit()
        raise HTTPException(400, "invalid_code")
    await db.commit()
    await service.grantStepUp(redis, request.cookies.get(COOKIE, ""))
    return StatusOut(enabled=True, backupCodesLeft=await service.backupLeft(db, user), stepUpActive=True)
