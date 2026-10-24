import uuid

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.sessions import COOKIE, getSessionUser
from app.db.redis import getRedis
from app.db.session import getDb


# zalogowany uzytkownik albo 401
async def getCurrentUser(
    request: Request, db: AsyncSession = Depends(getDb), redis: Redis = Depends(getRedis)
) -> User:
    sid = request.cookies.get(COOKIE)
    userId = await getSessionUser(redis, sid) if sid else None
    user = await db.get(User, uuid.UUID(userId)) if userId else None
    if not user:
        raise HTTPException(401, "not_authenticated")
    return user
