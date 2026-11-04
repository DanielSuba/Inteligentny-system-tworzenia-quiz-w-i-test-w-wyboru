import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.registry import registry
from app.apikeys.service import keyForUse
from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.common.safety import redact
from app.common.storage import Storage, getStorage
from app.config import getSettings
from app.db.redis import getRedis
from app.db.session import getDb
from app.generation import review, runner
from app.generation.models import GeneratedQuestion, GenerationJob
from app.generation.runner import PER_CALL_MATERIAL, PER_CALL_TOPIC
from app.generation.schemas import EstimateOut, GenQuestionOut, JobIn, JobOut
from app.generation.stale import expireStale
from app.generation.strategies import STRATEGIES
from app.generation.tasks import generateTask
from app.quizzes.convert import questionOut
from app.quizzes.schemas import QuestionIn, QuestionOut
from app.quizzes.service import getOwned
from app.sources.models import SourceChunk
from app.sources.service import getOwnDocument

router = APIRouter(tags=["generation"])

OUT_TOKENS_PER_QUESTION = 180


# szacunek tokenow i kosztu przed uruchomieniem (ceny z models.yaml, gdy sa znane)
async def estimate(db: AsyncSession, user: User, data: JobIn) -> EstimateOut:
    chunkTokens = 0
    if data.mode == "material":
        for docId in data.documentIds:
            doc = await getOwnDocument(db, user, docId)
            chunkTokens += min(doc.tokenCount, 800 * max(1, data.count // PER_CALL_MATERIAL + 1))
    calls = -(-data.count // (PER_CALL_MATERIAL if data.mode == "material" else PER_CALL_TOPIC))
    tokensIn = calls * 900 + chunkTokens  # instrukcja + przyklady na kazde wywolanie
    tokensOut = data.count * OUT_TOKENS_PER_QUESTION
    price = next((m for m in registry() if m["provider"] == data.provider and m["id"] == data.model), None)
    cost = None
    if price and price.get("priceIn") is not None and price.get("priceOut") is not None:
        cost = round((tokensIn * price["priceIn"] + tokensOut * price["priceOut"]) / 1_000_000, 4)
    if data.provider == "lmstudio":
        cost = 0.0
    return EstimateOut(tokensIn=tokensIn, tokensOut=tokensOut, costUsd=cost)


async def jobOut(db: AsyncSession, job: GenerationJob, withQuestions: bool) -> JobOut:
    out = JobOut.model_validate(job, from_attributes=True)
    if withQuestions:
        rows = await db.scalars(
            select(GeneratedQuestion).where(GeneratedQuestion.jobId == job.id).order_by(GeneratedQuestion.idx)
        )
        qs = []
        for g in rows.all():
            chunk = await db.get(SourceChunk, g.chunkId) if g.chunkId else None
            qs.append(
                GenQuestionOut.model_validate({**g.__dict__, "chunkText": chunk.text if chunk else None})
            )
        out.questions = qs
    return out


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@ Zadania generowania @@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@router.post("/generation/estimate")
async def estimateCost(
    data: JobIn, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> EstimateOut:
    await getOwned(db, user, data.quizId)
    return await estimate(db, user, data)


# start generowania: sprawdza dostep do quizu, materialow i klucza, potem wrzuca zadanie do kolejki
@router.post("/generation/jobs", status_code=201)
async def startJob(
    data: JobIn,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> JobOut:
    await getOwned(db, user, data.quizId)
    for docId in data.documentIds:
        await getOwnDocument(db, user, docId)
    keySource = "local"
    if data.provider != "lmstudio":
        found = await keyForUse(db, user.id, data.provider)
        if not found:
            raise HTTPException(400, "no_api_key")
        keySource = found[1]
        # dzienny limit dla kluczy systemowych
        if keySource == "system":
            day = f"daily:{user.id}:{date.today()}"
            if await redis.incr(day) > getSettings().systemDailyCalls:
                raise HTTPException(429, "daily_limit")
            await redis.expire(day, 86400)

    strategy = STRATEGIES[data.strategy]
    job = GenerationJob(
        userId=user.id,
        quizId=data.quizId,
        sourceMode=data.mode,
        strategy=data.strategy,
        provider=data.provider,
        model=data.model,
        keySource=keySource,
        promptVersion=f"{strategy.version}+system.v1+{data.mode}.v1",
        params=data.model_dump(
            mode="json", include={"count", "types", "difficulty", "language", "temperature", "topic", "focus"}
        ),
        documentIds=data.documentIds if data.mode == "material" else [],
        status="queued",
        progress=0,
        calls=0,
        tokensIn=0,
        tokensOut=0,
        durationMs=0,
        retries=0,
    )
    db.add(job)
    await db.commit()
    await generateTask.kiq(str(job.id))
    await db.refresh(job)
    return await jobOut(db, job, False)


@router.get("/generation/jobs")
async def listJobs(
    quizId: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> list[JobOut]:
    await getOwned(db, user, quizId)
    await expireStale(db)
    rows = await db.scalars(
        select(GenerationJob)
        .where(GenerationJob.quizId == quizId)
        .order_by(GenerationJob.createdAt.desc())
        .limit(20)
    )
    return [await jobOut(db, j, False) for j in rows.all()]


@router.get("/generation/jobs/{jobId}")
async def getJob(
    jobId: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> JobOut:
    await expireStale(db)
    job = await db.get(GenerationJob, jobId, populate_existing=True)
    if not job or job.userId != user.id:
        raise HTTPException(404, "job_not_found")
    return await jobOut(db, job, True)


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$ Recenzja $$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


@router.post("/generated/{gid}/accept")
async def acceptQuestion(
    gid: uuid.UUID,
    edited: QuestionIn | None = None,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuestionOut:
    return questionOut(await review.accept(db, user, gid, edited), store)


@router.post("/generated/{gid}/reject", status_code=204)
async def rejectQuestion(
    gid: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> None:
    await review.reject(db, user, gid)


# przyjmuje wszystkie poprawne pytania, ktore czekaja na recenzje
@router.post("/generation/jobs/{jobId}/accept-all")
async def acceptAll(
    jobId: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> dict:
    job = await db.get(GenerationJob, jobId)
    if not job or job.userId != user.id:
        raise HTTPException(404, "job_not_found")
    rows = await db.scalars(
        select(GeneratedQuestion.id).where(
            GeneratedQuestion.jobId == jobId,
            GeneratedQuestion.status == "pending",
            GeneratedQuestion.validationErrors == [],
        )
    )
    ids = list(rows.all())
    for gid in ids:
        await review.accept(db, user, gid, None)
    return {"accepted": len(ids)}


# nowa wersja jednego pytania (to samo zadanie, ten sam fragment materialu)
@router.post("/generated/{gid}/regenerate")
async def regenerate(
    gid: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> GenQuestionOut:
    g, job = await review.getOwnGenerated(db, user, gid)
    if g.status != "pending":
        raise HTTPException(409, "already_reviewed")
    try:
        new = await runner.regenerateOne(db, job, g)
    except RuntimeError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(502, "model_error") from Exception(redact(str(e)))
    chunk = await db.get(SourceChunk, new.chunkId) if new.chunkId else None
    return GenQuestionOut.model_validate({**new.__dict__, "chunkText": chunk.text if chunk else None})
