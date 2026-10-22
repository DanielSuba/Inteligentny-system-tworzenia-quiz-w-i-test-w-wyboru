from fastapi import APIRouter, Depends, Response
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import getRedis
from app.db.session import getDb

router = APIRouter(tags=["health"])


# sprawdza, czy baza odpowiada
async def checkDb(db: AsyncSession = Depends(getDb)) -> bool:
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# sprawdza, czy Redis odpowiada
async def checkRedis(redis: Redis = Depends(getRedis)) -> bool:
    try:
        return bool(await redis.ping())
    except Exception:
        return False


# stan backendu i usług, z których korzysta
@router.get("/health")
async def health(response: Response, dbOk: bool = Depends(checkDb), redisOk: bool = Depends(checkRedis)):
    allOk = dbOk and redisOk
    if not allOk:
        response.status_code = 503
    return {
        "status": "ok" if allOk else "error",
        "db": "ok" if dbOk else "error",
        "redis": "ok" if redisOk else "error",
    }
