import math
import time
import uuid
from datetime import UTC, datetime

from rapidfuzz import fuzz
from sqlalchemy import select

from app.ai.embeddings import cosine, embed
from app.apikeys.service import keyForUse
from app.common.safety import redact
from app.db.session import makeSession
from app.generation import checks, llm
from app.generation.models import GeneratedQuestion, GenerationJob
from app.generation.strategies import STRATEGIES, GenRequest
from app.quizzes.models import Question
from app.sources.models import SourceChunk
from app.sources.service import chunksOf

PER_CALL_MATERIAL = 5  # pytan na jeden fragment materialu
PER_CALL_TOPIC = 10


# wybiera fragmenty: wedlug tematow przewodnich (embeddingi albo tekst) albo rowno z calego materialu
async def pickChunks(chunks: list[SourceChunk], focus: str, n: int) -> list[SourceChunk]:
    if not chunks:
        return []
    if focus.strip():
        vec = await embed([focus])
        if vec and all(c.embedding is not None for c in chunks):
            ranked = sorted(chunks, key=lambda c: cosine(vec[0], list(c.embedding)), reverse=True)
        else:
            ranked = sorted(
                chunks, key=lambda c: fuzz.partial_ratio(focus.lower(), c.text.lower()), reverse=True
            )
        picked = ranked[:n]
    else:
        step = len(chunks) / n
        picked = (
            [chunks[min(int(i * step), len(chunks) - 1)] for i in range(n)] if n < len(chunks) else chunks
        )
    # gdy fragmentow jest mniej niz wywolan, uzywamy ich po kilka razy
    return [picked[i % len(picked)] for i in range(n)]


# plan wywolan: lista (fragment albo None, liczba pytan)
async def plan(job: GenerationJob, db) -> list[tuple[SourceChunk | None, int]]:
    count = job.params["count"]
    per = PER_CALL_MATERIAL if job.sourceMode == "material" else PER_CALL_TOPIC
    calls = math.ceil(count / per)
    sizes = [per] * (calls - 1) + [count - per * (calls - 1)]
    if job.sourceMode == "topic":
        return [(None, s) for s in sizes]
    chunks = await pickChunks(await chunksOf(db, job.documentIds), job.params.get("focus", ""), calls)
    return list(zip(chunks, sizes, strict=True))


# zapisuje jedno pytanie z wynikami sprawdzen (cytat, duplikat, reguly typu)
async def store(db, job, idx, q: dict, chunk, known: list) -> GeneratedQuestion:
    _, errors = checks.toQuestionIn(q)
    grounded = score = None
    if chunk is not None:
        grounded, score = checks.grounding(q.get("sourceQuote", ""), chunk.text)
    vec = (await embed([q.get("question", "")]) or [None])[0]
    dup = checks.findDuplicate(q.get("question", ""), vec, known)
    known.append((q.get("question", ""), vec))
    g = GeneratedQuestion(
        jobId=job.id,
        idx=idx,
        chunkId=chunk.id if chunk else None,
        rawOutput=q,
        parsed=q,
        grounded=grounded,
        groundingScore=score,
        duplicateOf=dup[:500] if dup else None,
        validationErrors=errors,
    )
    db.add(g)
    return g


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@ Glowna petla zadania @@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def runJob(jobId: uuid.UUID) -> None:
    async with makeSession() as db:
        job = await db.get(GenerationJob, jobId)
        if not job or job.status != "queued":
            return
        job.status = "running"
        await db.commit()
        start = time.monotonic()
        try:
            key = None
            if job.provider != "lmstudio":
                found = await keyForUse(db, job.userId, job.provider)
                key = found[0] if found else None
                if not key:
                    raise RuntimeError("no_api_key")
            strategy = STRATEGIES[job.strategy]
            p = job.params
            steps = await plan(job, db)
            existing = await db.scalars(select(Question.text).where(Question.quizId == job.quizId))
            known = [(t, None) for t in existing.all()]
            idx, failures, costs = 0, [], []

            for n, (chunk, size) in enumerate(steps):
                req = GenRequest(
                    size, p["types"], p["difficulty"], p["language"], p.get("focus", ""), p.get("topic", "")
                )
                try:
                    res = await llm.callModel(
                        job.provider,
                        job.model,
                        key,
                        strategy.messages(req, chunk.text if chunk else None),
                        p["temperature"],
                    )
                except Exception as e:
                    failures.append(redact(str(e))[:300])
                    job.calls += 1
                    continue
                job.calls += 1
                job.tokensIn += res.tokensIn
                job.tokensOut += res.tokensOut
                job.retries += res.retries
                job.actualProvider = res.actualProvider or job.actualProvider
                if res.cost is not None:
                    costs.append(res.cost)
                for q in res.raw["questions"]:
                    await store(db, job, idx, q, chunk, known)
                    idx += 1
                job.progress = round(100 * (n + 1) / len(steps))
                await db.commit()

            job.costUsd = round(sum(costs), 6) if costs else None
            job.error = "; ".join(failures) or None
            job.status = "done" if idx else "error"
        except Exception as e:
            job.status, job.error = "error", redact(str(e))[:1000]
        job.durationMs = int((time.monotonic() - start) * 1000)
        job.finishedAt = datetime.now(UTC)
        job.progress = 100
        await db.commit()


# nowa wersja jednego pytania (ten sam fragment materialu); stare oznaczane jako zastapione
async def regenerateOne(db, job: GenerationJob, old: GeneratedQuestion) -> GeneratedQuestion:
    key = None
    if job.provider != "lmstudio":
        found = await keyForUse(db, job.userId, job.provider)
        if not found:
            raise RuntimeError("no_api_key")
        key = found[0]
    p = job.params
    chunk = await db.get(SourceChunk, old.chunkId) if old.chunkId else None
    req = GenRequest(1, p["types"], p["difficulty"], p["language"], p.get("focus", ""), p.get("topic", ""))
    messages = STRATEGIES[job.strategy].messages(req, chunk.text if chunk else None)
    res = await llm.callModel(job.provider, job.model, key, messages, p["temperature"])
    job.calls += 1
    job.tokensIn += res.tokensIn
    job.tokensOut += res.tokensOut
    job.retries += res.retries
    rows = await db.scalars(select(GeneratedQuestion).where(GeneratedQuestion.jobId == job.id))
    others = [g for g in rows.all() if g.id != old.id and g.status != "replaced"]
    known = [(g.parsed.get("question", ""), None) for g in others]
    new = await store(
        db, job, max([g.idx for g in others] + [old.idx]) + 1, res.raw["questions"][0], chunk, known
    )
    old.status = "replaced"
    await db.commit()
    return new
