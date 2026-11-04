import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.common.storage import Storage, getStorage
from app.db.session import getDb
from app.learn import service
from app.learn.models import LearningSession
from app.learn.schemas import (
    AnswerIn,
    AnswerOut,
    NextOut,
    PlayOption,
    PlayQuestion,
    SessionOut,
    StartIn,
    Stats,
)
from app.media.service import toOut as mediaOut
from app.quizzes.models import Question, Quiz

router = APIRouter(tags=["learn"])


def sessionOut(s: LearningSession, quiz: Quiz, stats: Stats) -> SessionOut:
    return SessionOut(
        id=s.id,
        quizId=quiz.id,
        quizTitle=quiz.title,
        startedAt=s.startedAt,
        endedAt=s.endedAt,
        answered=s.answered,
        correct=s.correct,
        stats=stats,
    )


def playOut(q: Question, box: int | None, store: Storage) -> PlayQuestion:
    return PlayQuestion(
        id=q.id,
        type=q.type,
        text=q.text,
        media=mediaOut(q.media, store) if q.media else None,
        options=[PlayOption(id=o.id, text=o.text) for o in q.options],
        box=box,
    )


# sesja trwa tylko, dopoki quiz jest nadal dostepny (wlasny, publiczny albo z linkiem)
async def openSession(db: AsyncSession, user: User, sessionId: uuid.UUID) -> tuple[LearningSession, Quiz]:
    s = await service.ownSession(db, user, sessionId)
    quiz = await db.get(Quiz, s.quizId)
    if not quiz or not (quiz.ownerId == user.id or quiz.visibility in ("public", "unlisted")):
        raise HTTPException(404, "quiz_not_found")
    if s.endedAt:
        raise HTTPException(409, "session_ended")
    return s, quiz


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Sesja @@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@router.post("/learn/sessions", status_code=201)
async def startSession(
    data: StartIn, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> SessionOut:
    quiz = await service.quizForLearning(db, user, data.quizId, data.token)
    if not quiz.questions:
        raise HTTPException(409, "quiz_empty")
    s = await service.start(db, user, quiz)
    return sessionOut(s, quiz, await service.quizStats(db, user, quiz))


@router.get("/learn/sessions/{sessionId}/next")
async def nextQuestion(
    sessionId: uuid.UUID,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> NextOut:
    s, quiz = await openSession(db, user, sessionId)
    progress = await service.progressMap(db, user.id, quiz)
    q = await service.nextQuestion(db, s, quiz, progress)
    p = progress.get(q.id) if q else None
    return NextOut(
        question=playOut(q, p.box if p else None, store) if q else None,
        stats=service.statsOf(quiz, progress),
    )


@router.post("/learn/sessions/{sessionId}/answer")
async def answer(
    sessionId: uuid.UUID,
    data: AnswerIn,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
) -> AnswerOut:
    s, quiz = await openSession(db, user, sessionId)
    # odpowiedz tylko na pokazane pytanie (bez zgadywania innych przez API)
    if s.currentId != data.questionId:
        raise HTTPException(409, "not_current_question")
    q = next((x for x in quiz.questions if x.id == data.questionId), None)
    if not q:
        raise HTTPException(404, "question_not_found")
    ok, prevBox, box = await service.answer(db, user, s, q, data)
    oa = q.openAnswer
    return AnswerOut(
        correct=ok,
        correctOptionIds=[o.id for o in q.options if o.isCorrect],
        accepted=oa.accepted if oa else [],
        explanation=q.explanation,
        sourceQuote=q.sourceQuote,
        prevBox=prevBox,
        box=box,
        answered=s.answered,
        correctCount=s.correct,
        stats=await service.quizStats(db, user, quiz),
    )


@router.post("/learn/sessions/{sessionId}/end")
async def endSession(
    sessionId: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> SessionOut:
    s = await service.ownSession(db, user, sessionId)
    quiz = await db.get(Quiz, s.quizId)
    if not quiz:
        raise HTTPException(404, "quiz_not_found")
    await service.end(db, s)
    return sessionOut(s, quiz, await service.quizStats(db, user, quiz))


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Postep @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@router.get("/learn/quizzes/{quizId}/progress")
async def progress(
    quizId: uuid.UUID,
    token: str | None = None,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
) -> Stats:
    quiz = await service.quizForLearning(db, user, quizId, token)
    return await service.quizStats(db, user, quiz)


@router.delete("/learn/quizzes/{quizId}/progress", status_code=204)
async def resetProgress(
    quizId: uuid.UUID,
    token: str | None = None,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
) -> None:
    quiz = await service.quizForLearning(db, user, quizId, token)
    await service.resetProgress(db, user, quiz)
