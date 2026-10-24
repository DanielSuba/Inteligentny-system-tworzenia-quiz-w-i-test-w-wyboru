from app.common.health import checkDb, checkRedis
from app.main import app


# test na prawdziwej bazie i Redisie (wymaga docker compose up)
async def test_health_ok(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "db": "ok", "redis": "ok"}


# baza nie odpowiada -> 503 i informacja, co nie dziala
async def test_health_db_down(client):
    app.dependency_overrides[checkDb] = lambda: False
    app.dependency_overrides[checkRedis] = lambda: True
    res = await client.get("/api/health")
    assert res.status_code == 503
    assert res.json() == {"status": "error", "db": "error", "redis": "ok"}


async def test_health_redis_down(client):
    app.dependency_overrides[checkDb] = lambda: True
    app.dependency_overrides[checkRedis] = lambda: False
    res = await client.get("/api/health")
    assert res.status_code == 503
    assert res.json()["redis"] == "error"
