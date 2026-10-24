import asyncio
import os
import re
import tempfile

import asyncpg
import pytest

from app.config import Settings

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@ Osobna baza i Redis @@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# testy dzialaja na bazie quizforge_test i Redisie nr 15, zeby nie ruszac danych z pracy
baseUrl = Settings().databaseUrl
testUrl = baseUrl.rsplit("/", 1)[0] + "/quizforge_test"
os.environ["DATABASE_URL"] = testUrl
os.environ["REDIS_URL"] = re.sub(r"/\d+$", "", Settings().redisUrl) + "/15"
os.environ["STORAGE_DIR"] = tempfile.mkdtemp(prefix="qf-test-")
os.environ["APP_ENV"] = "test"

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.common import mail  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.base import Base  # noqa: E402
from app.db.redis import redis  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


# tworzy baze testowa (jesli jej nie ma) i swieze tabele
async def prepareDb() -> None:
    plain = baseUrl.replace("+asyncpg", "")
    conn = await asyncpg.connect(plain)
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'quizforge_test'")
    if not exists:
        await conn.execute("CREATE DATABASE quizforge_test")
    await conn.close()
    async with engine.begin() as c:
        await c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)


def pytest_sessionstart(session):
    asyncio.run(prepareDb())
    asyncio.run(engine.dispose())


# czysci tabele i Redis przed kazdym testem
@pytest.fixture(autouse=True)
async def clean():
    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as c:
        await c.execute(text(f"TRUNCATE {names} CASCADE"))
    await redis.flushdb()
    yield


# e-maile nie sa wysylane, tylko zbierane do listy
@pytest.fixture(autouse=True)
def outbox(monkeypatch):
    sent = []

    async def fakeSend(to, subject, body):
        sent.append({"to": to, "subject": subject, "text": body})

    monkeypatch.setattr(mail, "sendMail", fakeSend)
    return sent


# klient HTTP z ciasteczkiem i naglowkiem CSRF
async def makeClient() -> AsyncClient:
    c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    await c.get("/api/health")
    c.headers["x-csrf-token"] = c.cookies["qf_csrf"]
    return c


@pytest.fixture
async def client():
    c = await makeClient()
    yield c
    await c.aclose()
    app.dependency_overrides.clear()


# drugi klient = drugie urzadzenie tego samego uzytkownika
@pytest.fixture
async def other():
    c = await makeClient()
    yield c
    await c.aclose()
