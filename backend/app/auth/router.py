import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.models import User
from app.auth.schemas import EmailIn, LoginIn, RegisterIn, ResetIn, StatusOut, TokenIn
from app.auth.security import DUMMY_HASH, checkPassword, hashToken
from app.auth.sessions import (
    COOKIE,
    clearSessionCookie,
    createSession,
    deleteSession,
    deleteUserSessions,
    setSessionCookie,
)
from app.common.ratelimit import rateLimit
from app.config import getSettings
from app.db.redis import getRedis
from app.db.session import getDb
from app.profile.schemas import MeOut
from app.profile.service import getMe
from app.security.audit import audit
from app.twofactor import service as twofactor
from app.twofactor.schemas import CodeIn

router = APIRouter(prefix="/auth", tags=["auth"])

# logowanie z 2FA czeka na kod w Redisie (5 minut), ciasteczko wiaze to z przegladarka
PENDING = "2fa:"
PENDING_S = 300
PENDING_COOKIE = "qf_2fa"

# jedna odpowiedz dla wysylek maili, zeby nie zdradzac, czy konto istnieje
CHECK_EMAIL = StatusOut(status="check_email")


@router.post("/register", status_code=201, dependencies=[Depends(rateLimit("register", 5, 3600))])
async def register(data: RegisterIn, db: AsyncSession = Depends(getDb)) -> StatusOut:
    await service.register(db, data)
    return CHECK_EMAIL


@router.post("/verify-email")
async def verifyEmail(data: TokenIn, db: AsyncSession = Depends(getDb)) -> StatusOut:
    await service.verifyEmail(db, data.token)
    return StatusOut(status="ok")


@router.post("/resend-verification", dependencies=[Depends(rateLimit("resend", 5, 3600))])
async def resendVerification(data: EmailIn, db: AsyncSession = Depends(getDb)) -> StatusOut:
    await service.resendVerification(db, data.email)
    return CHECK_EMAIL


# logowanie: sprawdza haslo, tworzy nowa sesje (stara jest usuwana)
@router.post("/login", dependencies=[Depends(rateLimit("login", 10, 900))])
async def login(
    data: LoginIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> MeOut | StatusOut:
    user = await service.findUser(db, data.email)
    passOk = checkPassword(data.password, user.passwordHash if user else DUMMY_HASH)
    if not user or not passOk:
        raise HTTPException(401, "invalid_credentials")
    if not user.emailVerifiedAt:
        raise HTTPException(403, "email_not_verified")

    # konto z 2FA: najpierw kod, sesja powstaje dopiero po nim
    if user.totpEnabledAt:
        pending = secrets.token_urlsafe(32)
        await redis.set(PENDING + hashToken(pending), str(user.id), ex=PENDING_S)
        response.set_cookie(
            PENDING_COOKIE,
            pending,
            max_age=PENDING_S,
            httponly=True,
            secure=getSettings().isProd,
            samesite="lax",
            path="/api/auth",
        )
        return StatusOut(status="2fa_required")
    return await startSession(request, response, db, redis, user)


# nowa sesja po poprawnym logowaniu (stara jest usuwana)
async def startSession(request: Request, response: Response, db: AsyncSession, redis: Redis, user) -> MeOut:
    oldSid = request.cookies.get(COOKIE)
    if oldSid:
        await deleteSession(redis, oldSid)
    setSessionCookie(response, await createSession(redis, str(user.id)))
    return await getMe(db, user)


# drugi krok logowania: kod z aplikacji albo kod zapasowy (najwyzej 5 prob)
@router.post("/login/2fa", dependencies=[Depends(rateLimit("login-2fa", 10, 900))])
async def login2fa(
    data: CodeIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> MeOut:
    pending = request.cookies.get(PENDING_COOKIE)
    key = PENDING + hashToken(pending) if pending else ""
    userId = await redis.get(key) if key else None
    if not userId:
        raise HTTPException(401, "2fa_expired")
    user = await db.get(User, uuid.UUID(userId))
    if not await twofactor.checkCode(db, redis, user, data.code):
        tries = await redis.incr(key + ":tries")
        await redis.expire(key + ":tries", PENDING_S)
        if tries >= 5:
            await redis.delete(key)
        audit(db, request, user, "login_2fa_failed")
        await db.commit()
        raise HTTPException(400, "invalid_code")
    await redis.delete(key, key + ":tries")
    response.delete_cookie(PENDING_COOKIE, path="/api/auth")
    await db.commit()
    return await startSession(request, response, db, redis, user)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, redis: Redis = Depends(getRedis)) -> None:
    sid = request.cookies.get(COOKIE)
    if sid:
        await deleteSession(redis, sid)
    clearSessionCookie(response)


@router.post("/forgot-password", dependencies=[Depends(rateLimit("forgot", 5, 3600))])
async def forgotPassword(data: EmailIn, db: AsyncSession = Depends(getDb)) -> StatusOut:
    await service.forgotPassword(db, data.email)
    return CHECK_EMAIL


# nowe haslo z linku; wylogowuje wszystkie sesje uzytkownika
@router.post("/reset-password", dependencies=[Depends(rateLimit("reset", 10, 3600))])
async def resetPassword(
    data: ResetIn, db: AsyncSession = Depends(getDb), redis: Redis = Depends(getRedis)
) -> StatusOut:
    user = await service.resetPassword(db, data.token, data.password)
    await deleteUserSessions(redis, str(user.id))
    return StatusOut(status="ok")
