import uuid

from fastapi import HTTPException
from rapidfuzz.distance import Levenshtein
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.generation import checks
from app.generation.models import GeneratedQuestion, GenerationJob, QuestionReview
from app.quizzes import service as quizService
from app.quizzes.models import Question
from app.quizzes.schemas import QuestionIn


# wygenerowane pytanie z zadania uzytkownika albo 404
async def getOwnGenerated(
    db: AsyncSession, user: User, gid: uuid.UUID
) -> tuple[GeneratedQuestion, GenerationJob]:
    g = await db.get(GeneratedQuestion, gid, populate_existing=True)
    job = await db.get(GenerationJob, g.jobId, populate_existing=True) if g else None
    if not g or not job or job.userId != user.id:
        raise HTTPException(404, "generated_not_found")
    return g, job


# przyjecie pytania (bez zmian albo po edycji): trafia do quizu jako pytanie z AI
async def accept(db: AsyncSession, user: User, gid: uuid.UUID, edited: QuestionIn | None) -> Question:
    g, job = await getOwnGenerated(db, user, gid)
    if g.status != "pending":
        raise HTTPException(409, "already_reviewed")
    original, errors = checks.toQuestionIn(g.parsed)
    final = edited or original
    if final is None:
        raise HTTPException(422, "generated_invalid")
    # wartosci zapamietane przed zapisem (addQuestion odswieza obiekty sesji)
    jobId, quizId, chunkId, parsed = job.id, job.quizId, g.chunkId, dict(g.parsed)
    finalDict = final.model_dump(mode="json")
    changed = edited is not None and checks.asText(finalDict) != checks.asText(
        original.model_dump() if original else parsed
    )
    status = "edited" if changed else "accepted"

    q = await quizService.addQuestion(db, user, quizId, final)
    qid = q.id
    q.origin, q.generationJobId, q.sourceChunkId = "ai", jobId, chunkId
    q.sourceQuote = parsed.get("sourceQuote") or None
    g = await db.get(GeneratedQuestion, gid)
    g.status = status
    db.add(
        QuestionReview(
            generatedQuestionId=gid,
            status=status,
            final=finalDict,
            editDistance=Levenshtein.distance(checks.asText(parsed), checks.asText(finalDict))
            if changed
            else 0,
            questionId=qid,
        )
    )
    await db.commit()
    return await db.get(Question, qid, populate_existing=True)


async def reject(db: AsyncSession, user: User, gid: uuid.UUID) -> None:
    g, _ = await getOwnGenerated(db, user, gid)
    if g.status != "pending":
        raise HTTPException(409, "already_reviewed")
    g.status = "rejected"
    db.add(QuestionReview(generatedQuestionId=g.id, status="rejected"))
    await db.commit()
