import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import getCurrentUser, getOptionalUser
from app.auth.models import User
from app.common.storage import Storage, getStorage
from app.db.session import getDb
from app.quizzes import service
from app.quizzes.checking import checkOpen
from app.quizzes.convert import questionOut, quizDetail, quizOut
from app.quizzes.models import Question
from app.quizzes.schemas import (
    CheckIn,
    OrderIn,
    QuestionIn,
    QuestionOut,
    QuizDetail,
    QuizIn,
    QuizOut,
    QuizUpdate,
)

router = APIRouter(tags=["quizzes"])


async def detail(db: AsyncSession, quiz, user, store: Storage) -> QuizDetail:
    return quizDetail(quiz, user, await service.authorName(db, quiz.ownerId), store)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Quizy @@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@router.get("/quizzes")
async def listQuizzes(
    q: str = "",
    visibility: Literal["public", "unlisted", "friends", "private"] | None = None,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> list[QuizOut]:
    rows = await service.listMine(db, user, q, visibility)
    name = await service.authorName(db, user.id)
    return [quizOut(quiz, user, name, n, store) for quiz, n in rows]


@router.post("/quizzes", status_code=201)
async def createQuiz(
    data: QuizIn,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuizDetail:
    return await detail(db, await service.createQuiz(db, user, data), user, store)


@router.get("/quizzes/{quizId}")
async def getQuiz(
    quizId: uuid.UUID,
    user: User | None = Depends(getOptionalUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuizDetail:
    return await detail(db, await service.getForView(db, user, quizId), user, store)


@router.patch("/quizzes/{quizId}")
async def updateQuiz(
    quizId: uuid.UUID,
    data: QuizUpdate,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuizDetail:
    return await detail(db, await service.updateQuiz(db, user, quizId, data), user, store)


@router.delete("/quizzes/{quizId}", status_code=204)
async def deleteQuiz(
    quizId: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> None:
    await service.deleteQuiz(db, user, quizId)


@router.post("/quizzes/{quizId}/share-token")
async def newShareToken(
    quizId: uuid.UUID,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuizDetail:
    return await detail(db, await service.newShareToken(db, user, quizId), user, store)


@router.put("/quizzes/{quizId}/order")
async def reorder(
    quizId: uuid.UUID,
    data: OrderIn,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuizDetail:
    return await detail(db, await service.reorder(db, user, quizId, data.ids), user, store)


# quiz z linku udostepniania (dziala tez dla gosci)
@router.get("/shared/{token}")
async def getShared(
    token: str,
    user: User | None = Depends(getOptionalUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuizDetail:
    return await detail(db, await service.getShared(db, user, token), user, store)


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$ Pytania $$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


@router.post("/quizzes/{quizId}/questions", status_code=201)
async def addQuestion(
    quizId: uuid.UUID,
    data: QuestionIn,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuestionOut:
    return questionOut(await service.addQuestion(db, user, quizId, data), store)


@router.put("/questions/{questionId}")
async def updateQuestion(
    questionId: uuid.UUID,
    data: QuestionIn,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuestionOut:
    return questionOut(await service.updateQuestion(db, user, questionId, data), store)


@router.delete("/questions/{questionId}", status_code=204)
async def deleteQuestion(
    questionId: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> None:
    await service.deleteQuestion(db, user, questionId)


@router.post("/questions/{questionId}/duplicate", status_code=201)
async def duplicateQuestion(
    questionId: uuid.UUID,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> QuestionOut:
    return questionOut(await service.duplicateQuestion(db, user, questionId), store)


# sprawdza odpowiedz na pytanie otwarte (podglad quizu; ta sama funkcja posluzy w grze)
@router.post("/questions/{questionId}/check")
async def checkAnswer(
    questionId: uuid.UUID,
    data: CheckIn,
    token: str | None = None,
    user: User | None = Depends(getOptionalUser),
    db: AsyncSession = Depends(getDb),
) -> dict:
    q = await db.get(Question, questionId)
    if not q:
        raise HTTPException(404, "question_not_found")
    # dostep jak do quizu: wlasciciel, quiz publiczny albo link udostepniania
    quiz = await service.getShared(db, user, token) if token else await service.getForView(db, user, q.quizId)
    if quiz.id != q.quizId:
        raise HTTPException(404, "question_not_found")
    oa = q.openAnswer
    ok = bool(oa) and checkOpen(data.odp, oa.accepted, oa.fuzzyThreshold, oa.caseSensitive, oa.ignoreAccents)
    return {"correct": ok}
