import secrets

from fastapi import Response
from redis.asyncio import Redis

from app.auth.security import hashToken
from app.config import getSettings

COOKIE = "qf_session"
SESS = "sess:"  # sess:<hash id> -> id uzytkownika
USER_SESS = "usess:"  # usess:<id uzytkownika> -> zbior hashy sesji


def ttl() -> int:
    return getSettings().sessionDays * 86400


# tworzy nowa sesje i zwraca jej id (to id trafia do ciasteczka)
async def createSession(redis: Redis, userId: str) -> str:
    sid = secrets.token_urlsafe(32)
    key = hashToken(sid)
    await redis.set(SESS + key, userId, ex=ttl())
    await redis.sadd(USER_SESS + userId, key)
    await redis.expire(USER_SESS + userId, ttl())
    return sid


# zwraca id uzytkownika z sesji i przedluza jej waznosc
async def getSessionUser(redis: Redis, sid: str) -> str | None:
    key = SESS + hashToken(sid)
    userId = await redis.get(key)
    if userId:
        await redis.expire(key, ttl())
    return userId


async def deleteSession(redis: Redis, sid: str) -> None:
    key = hashToken(sid)
    userId = await redis.get(SESS + key)
    await redis.delete(SESS + key)
    if userId:
        await redis.srem(USER_SESS + userId, key)


# wylogowuje uzytkownika wszedzie (oprocz sesji keepSid)
async def deleteUserSessions(redis: Redis, userId: str, keepSid: str | None = None) -> None:
    keep = hashToken(keepSid) if keepSid else None
    for key in await redis.smembers(USER_SESS + userId):
        if key != keep:
            await redis.delete(SESS + key)
            await redis.srem(USER_SESS + userId, key)


def setSessionCookie(response: Response, sid: str) -> None:
    response.set_cookie(
        COOKIE,
        sid,
        max_age=ttl(),
        httponly=True,
        secure=getSettings().isProd,
        samesite="lax",
        path="/",
    )


def clearSessionCookie(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")
