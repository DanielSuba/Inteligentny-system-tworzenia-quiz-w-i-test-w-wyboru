import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import getSettings
from app.db import models  # noqa: F401  (rejestruje tabele)
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# tu Alembic szuka tabel do porownania przy --autogenerate
target = Base.metadata
dbUrl = getSettings().databaseUrl


# tryb offline: generuje sam SQL bez laczenia z baza
def runOffline() -> None:
    context.configure(url=dbUrl, target_metadata=target, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def doRun(conn) -> None:
    context.configure(connection=conn, target_metadata=target)
    with context.begin_transaction():
        context.run_migrations()


# tryb online: laczy sie z baza i wykonuje migracje
async def runOnline() -> None:
    engine = create_async_engine(dbUrl)
    async with engine.connect() as conn:
        await conn.run_sync(doRun)
    await engine.dispose()


if context.is_offline_mode():
    runOffline()
else:
    asyncio.run(runOnline())
