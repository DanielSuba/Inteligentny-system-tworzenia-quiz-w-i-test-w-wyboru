from fastapi import APIRouter, Depends, HTTPException, Request, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.schemas import EmailIn, LoginIn, RegisterIn, ResetIn, StatusOut, TokenIn
from app.auth.security import DUMMY_HASH, checkPassword
from app.auth.sessions import (
    COOKIE,
    clearSessionCookie,
    createSession,
    deleteSession,
    deleteUserSessions,
    setSessionCookie,
)
from app.common.ratelimit import rateLimit
from app.db.redis import getRedis
from app.db.session import getDb
from app.profile.schemas import MeOut
from app.profile.service import getMe

router = APIRouter(prefix="/auth", tags=["auth"])

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
) -> MeOut:
    user = await service.findUser(db, data.email)
    passOk = checkPassword(data.password, user.passwordHash if user else DUMMY_HASH)
    if not user or not passOk:
        raise HTTPException(401, "invalid_credentials")
    if not user.emailVerifiedAt:
        raise HTTPException(403, "email_not_verified")

    oldSid = request.cookies.get(COOKIE)
    if oldSid:
        await deleteSession(redis, oldSid)
    setSessionCookie(response, await createSession(redis, str(user.id)))
    return await getMe(db, user)


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
