import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.db.session import makeSession
from app.generation import llm
from app.generation.llm import CallResult
from app.generation.models import GenerationJob
from app.generation.schemas import GenBatch
from app.generation.stale import interruptAll
from app.generation.tasks import broker
from tests.test_generation import jobBody, q, setup


@pytest.fixture(autouse=True)
async def fakeModel(monkeypatch):
    await broker.startup()

    async def fake(provider, model, key, messages, temperature):
        batch = GenBatch(questions=[q("Gdzie zachodzi fotosynteza?")])
        return CallResult(batch=batch, raw=batch.model_dump(), tokensIn=10, tokensOut=10, retries=0)

    monkeypatch.setattr(llm, "callModel", fake)


async def newJob(client, outbox) -> uuid.UUID:
    quiz, doc = await setup(client, outbox)
    job = (await client.post("/api/generation/jobs", json=jobBody(quiz, doc, count=1))).json()
    return uuid.UUID(job["id"])


# ustawia stan zadania tak, jakby worker padl w trakcie
async def setState(jobId, status, beatAgo: timedelta | None):
    async with makeSession() as db:
        job = await db.get(GenerationJob, jobId)
        job.status = status
        job.error = None
        job.heartbeatAt = datetime.now(UTC) - beatAgo if beatAgo else None
        await db.commit()


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@ Przerwane zadania @@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_worker_leaves_heartbeat(client, outbox):
    jobId = await newJob(client, outbox)
    async with makeSession() as db:
        job = await db.get(GenerationJob, jobId)
    assert job.status == "done" and job.heartbeatAt is not None


async def test_silent_running_job_becomes_interrupted(client, outbox):
    jobId = await newJob(client, outbox)
    await setState(jobId, "running", timedelta(minutes=20))
    job = (await client.get(f"/api/generation/jobs/{jobId}")).json()
    assert job["status"] == "error" and job["error"] == "interrupted"


async def test_alive_running_job_stays(client, outbox):
    jobId = await newJob(client, outbox)
    await setState(jobId, "running", timedelta(minutes=2))
    job = (await client.get(f"/api/generation/jobs/{jobId}")).json()
    assert job["status"] == "running"
    # lista zadan quizu tez sprzata, ale zywego zadania nie rusza
    listed = (await client.get("/api/generation/jobs", params={"quizId": job["quizId"]})).json()
    assert listed[0]["status"] == "running"


async def test_restart_with_memory_queue_interrupts_all(client, outbox):
    jobId = await newJob(client, outbox)
    await setState(jobId, "queued", None)
    async with makeSession() as db:
        assert await interruptAll(db) == 1
        job = await db.get(GenerationJob, jobId, populate_existing=True)
    assert job.status == "error" and job.error == "interrupted"
    # zakonczone zadania zostaja bez zmian
    async with makeSession() as db:
        assert await interruptAll(db) == 0
