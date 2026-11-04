import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.learn import algo
from app.learn.models import LearningProgress, LearningSession
from app.learn.schemas import AnswerIn, Stats
from app.quizzes import service as quizzes
from app.quizzes.checking import checkOpen
from app.quizzes.models import Question, Quiz

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Dostep @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# quiz do nauki: wlasny, publiczny albo z linku udostepniania
async def quizForLearning(db: AsyncSession, user: User, quizId: uuid.UUID, token: str | None) -> Quiz:
    if token:
        quiz = await quizzes.getShared(db, user, token)
        if quiz.id != quizId:
            raise HTTPException(404, "quiz_not_found")
        return quiz
    return await quizzes.getForView(db, user, quizId)


async def ownSession(db: AsyncSession, user: User, sessionId: uuid.UUID) -> LearningSession:
    s = await db.get(LearningSession, sessionId)
    if not s or s.userId != user.id:
        raise HTTPException(404, "session_not_found")
    return s


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Postep @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# postep ucznia w pytaniach quizu: {questionId: LearningProgress}
async def progressMap(db: AsyncSession, userId: uuid.UUID, quiz: Quiz) -> dict:
    ids = [q.id for q in quiz.questions]
    if not ids:
        return {}
    rows = await db.scalars(
        select(LearningProgress).where(
            LearningProgress.userId == userId, LearningProgress.questionId.in_(ids)
        )
    )
    return {p.questionId: p for p in rows.all()}


def statsOf(quiz: Quiz, progress: dict) -> Stats:
    boxes = [0] * (algo.BOXES + 1)
    for q in quiz.questions:
        p = progress.get(q.id)
        boxes[p.box if p else 0] += 1
    total = len(quiz.questions)
    mastered = sum(boxes[algo.MASTERED_BOX :])
    return Stats(
        total=total, boxes=boxes, mastered=mastered, masteredPct=round(100 * mastered / total) if total else 0
    )


async def quizStats(db: AsyncSession, user: User, quiz: Quiz) -> Stats:
    return statsOf(quiz, await progressMap(db, user.id, quiz))


async def resetProgress(db: AsyncSession, user: User, quiz: Quiz) -> None:
    ids = [q.id for q in quiz.questions]
    if ids:
        await db.execute(
            delete(LearningProgress).where(
                LearningProgress.userId == user.id, LearningProgress.questionId.in_(ids)
            )
        )
        await db.commit()


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Sesja @@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def start(db: AsyncSession, user: User, quiz: Quiz) -> LearningSession:
    s = LearningSession(userId=user.id, quizId=quiz.id, recent=[])
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


# losuje nastepne pytanie (to samo, dopoki uczen nie odpowie)
async def nextQuestion(db: AsyncSession, s: LearningSession, quiz: Quiz, progress: dict) -> Question | None:
    byId = {q.id: q for q in quiz.questions}
    if s.currentId in byId:
        return byId[s.currentId]
    cards = [
        algo.Card(q.id, progress[q.id].box, progress[q.id].lastSeenAt)
        if q.id in progress
        else algo.Card(q.id)
        for q in quiz.questions
    ]
    card = algo.pick(cards, list(s.recent or []), datetime.now(UTC))
    if not card:
        return None
    s.currentId = card.id
    s.recent = algo.remember(list(s.recent or []), card.id)
    await db.commit()
    return byId[card.id]


# sprawdza odpowiedz na serwerze (uczen nie zna poprawnych odpowiedzi przed wyslaniem)
def isCorrect(q: Question, data: AnswerIn) -> bool:
    if q.type == "open":
        oa = q.openAnswer
        return bool(oa) and checkOpen(
            data.odp, oa.accepted, oa.fuzzyThreshold, oa.caseSensitive, oa.ignoreAccents
        )
    good = {o.id for o in q.options if o.isCorrect}
    return set(data.optionIds) == good


# zapisuje wynik: pudelko Leitnera, liczniki, statystyki sesji
async def answer(db: AsyncSession, user: User, s: LearningSession, q: Question, data: AnswerIn):
    ok = isCorrect(q, data)
    p = await db.get(LearningProgress, (user.id, q.id))
    prevBox = p.box if p else None
    if not p:
        p = LearningProgress(userId=user.id, questionId=q.id, correctCount=0, wrongCount=0)
        db.add(p)
    p.box = algo.nextBox(prevBox, ok)
    p.lastSeenAt = datetime.now(UTC)
    p.lastResult = ok
    if ok:
        p.correctCount += 1
    else:
        p.wrongCount += 1
    s.answered += 1
    s.correct += int(ok)
    s.currentId = None
    await db.commit()
    return ok, prevBox, p.box


async def end(db: AsyncSession, s: LearningSession) -> None:
    if not s.endedAt:
        s.endedAt = datetime.now(UTC)
        s.currentId = None
        await db.commit()
