from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import getSettings

engine = create_async_engine(getSettings().databaseUrl, pool_pre_ping=True)
makeSession = async_sessionmaker(engine, expire_on_commit=False)


# daje sesje bazy na czas jednego zapytania HTTP
async def getDb() -> AsyncIterator[AsyncSession]:
    async with makeSession() as db:
        yield db
