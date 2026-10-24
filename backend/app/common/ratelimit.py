from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from app.db.redis import getRedis


# limit prob na adres IP: najwyzej `limit` zapytan w oknie `windowS` sekund
def rateLimit(action: str, limit: int, windowS: int):
    async def check(request: Request, redis: Redis = Depends(getRedis)) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{action}:{ip}"
        n = await redis.incr(key)
        if n == 1:
            await redis.expire(key, windowS)
        if n > limit:
            raise HTTPException(429, "too_many_requests")

    return check
