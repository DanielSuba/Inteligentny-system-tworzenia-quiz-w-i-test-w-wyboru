from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, update

from app.generation.models import GenerationJob

# zadanie bez znaku zycia dluzej niz tyle uznajemy za przerwane (awaria workera, restart API)
STALE_AFTER = timedelta(minutes=15)
INTERRUPTED = "interrupted"


# oznacza wiszace zadania jako przerwane; zwraca ich liczbe
async def expireStale(db) -> int:
    limit = datetime.now(UTC) - STALE_AFTER
    res = await db.execute(
        update(GenerationJob)
        .where(
            GenerationJob.status == "running",
            func.coalesce(GenerationJob.heartbeatAt, GenerationJob.createdAt) < limit,
        )
        .values(status="error", error=INTERRUPTED, finishedAt=func.now(), progress=100)
    )
    await db.commit()
    return res.rowcount


# kolejka w pamieci procesu: po starcie API stare zadania juz nigdy sie nie wykonaja
async def interruptAll(db) -> int:
    res = await db.execute(
        update(GenerationJob)
        .where(or_(GenerationJob.status == "queued", GenerationJob.status == "running"))
        .values(status="error", error=INTERRUPTED, finishedAt=func.now(), progress=100)
    )
    await db.commit()
    return res.rowcount
