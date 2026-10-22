from redis.asyncio import Redis

from app.config import getSettings

redis = Redis.from_url(getSettings().redisUrl, decode_responses=True)


def getRedis() -> Redis:
    return redis
