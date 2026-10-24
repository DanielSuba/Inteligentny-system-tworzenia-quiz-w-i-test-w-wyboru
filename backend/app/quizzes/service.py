import secrets
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import any_, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload

from app.auth.models import User
from app.media.models import Media
from app.profile.models import Profile
from app.quizzes.models import AnswerOption, OpenAnswer, Question, Quiz
from app.quizzes.schemas import QuestionIn, QuizIn, QuizUpdate

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@ Dostep @@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def authorName(db: AsyncSession, userId: uuid.UUID) -> str:
    return await db.scalar(select(Profile.displayName).where(Profile.userId == userId)) or "?"


# quiz do odczytu: wlasciciel albo quiz publiczny; inaczej 404 (nie zdradzamy, ze istnieje)
async def getForView(db: AsyncSession, user: User | None, quizId: uuid.UUID) -> Quiz:
    quiz = await db.get(Quiz, quizId)
    isOwner = quiz is not None and user is not None and quiz.ownerId == user.id
    if not quiz or not (isOwner or quiz.visibility == "public"):
        raise HTTPException(404, "quiz_not_found")
    return quiz


# quiz z linku udostepniania (publiczny albo "tylko z linkiem")
async def getShared(db: AsyncSession, user: User | None, token: str) -> Quiz:
    quiz = await db.scalar(select(Quiz).where(Quiz.shareToken == token))
    isOwner = quiz is not None and user is not None and quiz.ownerId == user.id
    if not quiz or not (isOwner or quiz.visibility in ("public", "unlisted")):
        raise HTTPException(404, "quiz_not_found")
    return quiz


# quiz do edycji: tylko wlasciciel
async def getOwned(db: AsyncSession, user: User, quizId: uuid.UUID) -> Quiz:
    quiz = await db.get(Quiz, quizId)
    if not quiz:
        raise HTTPException(404, "quiz_not_found")
    if quiz.ownerId != user.id:
        raise HTTPException(403, "forbidden")
    return quiz


# pytanie do edycji razem z jego quizem (tylko wlasciciel)
async def getOwnedQuestion(db: AsyncSession, user: User, questionId: uuid.UUID) -> tuple[Question, Quiz]:
    q = await db.get(Question, questionId)
    if not q:
        raise HTTPException(404, "question_not_found")
    return q, await getOwned(db, user, q.quizId)


# media moze dolaczyc tylko jego wlasciciel
async def checkMedia(db: AsyncSession, user: User, mediaId: uuid.UUID | None) -> None:
    if mediaId is None:
        return
    m = await db.get(Media, mediaId)
    if not m or m.ownerId != user.id:
        raise HTTPException(400, "invalid_media")


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$ Quizy $$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


# moje quizy z liczba pytan; szukanie po tytule i tagach
async def listMine(db: AsyncSession, user: User, q: str = "", visibility: str | None = None):
    counts = (
        select(Question.quizId.label("qid"), func.count().label("n")).group_by(Question.quizId).subquery()
    )
    stmt = (
        select(Quiz, func.coalesce(counts.c.n, 0))
        .options(lazyload(Quiz.questions))
        .outerjoin(counts, counts.c.qid == Quiz.id)
        .where(Quiz.ownerId == user.id)
        .order_by(Quiz.updatedAt.desc())
    )
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Quiz.title.ilike(like), literal(q.strip().lower()) == any_(Quiz.tags)))
    if visibility:
        stmt = stmt.where(Quiz.visibility == visibility)
    return (await db.execute(stmt)).all()


async def createQuiz(db: AsyncSession, user: User, data: QuizIn) -> Quiz:
    await checkMedia(db, user, data.coverMediaId)
    quiz = Quiz(ownerId=user.id, shareToken=secrets.token_urlsafe(12), **data.model_dump())
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz


async def updateQuiz(db: AsyncSession, user: User, quizId: uuid.UUID, data: QuizUpdate) -> Quiz:
    quiz = await getOwned(db, user, quizId)
    changes = data.model_dump(exclude_unset=True)
    if "coverMediaId" in changes:
        await checkMedia(db, user, changes["coverMediaId"])
    if changes.get("tags") is not None:
        changes["tags"] = QuizIn(title="x", tags=changes["tags"]).tags
    for field, value in changes.items():
        if value is not None or field == "coverMediaId":
            setattr(quiz, field, value)
    touch(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz


# nowy link udostepniania: stary przestaje dzialac
async def newShareToken(db: AsyncSession, user: User, quizId: uuid.UUID) -> Quiz:
    quiz = await getOwned(db, user, quizId)
    quiz.shareToken = secrets.token_urlsafe(12)
    touch(quiz)
    await db.commit()
    return quiz


async def deleteQuiz(db: AsyncSession, user: User, quizId: uuid.UUID) -> None:
    await db.delete(await getOwned(db, user, quizId))
    await db.commit()


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%% Pytania %%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# przepisuje dane z formularza do pytania (opcje i zasady otwartej odp. od nowa)
def fillQuestion(q: Question, data: QuestionIn) -> None:
    for field in ("type", "text", "explanation", "difficulty", "timeLimitS", "points", "category", "mediaId"):
        setattr(q, field, getattr(data, field))
    q.options = [
        AnswerOption(position=i, text=o.text.strip(), isCorrect=o.isCorrect)
        for i, o in enumerate(data.options)
    ]
    q.openAnswer = (
        OpenAnswer(
            accepted=data.accepted,
            fuzzyThreshold=data.fuzzyThreshold,
            caseSensitive=data.caseSensitive,
            ignoreAccents=data.ignoreAccents,
        )
        if data.type == "open"
        else None
    )


# data ostatniej zmiany ustawiana recznie (po zmianie pytan tez)
def touch(quiz: Quiz) -> None:
    quiz.updatedAt = datetime.now(UTC)


async def addQuestion(db: AsyncSession, user: User, quizId: uuid.UUID, data: QuestionIn) -> Question:
    quiz = await getOwned(db, user, quizId)
    await checkMedia(db, user, data.mediaId)
    q = Question(quizId=quiz.id, position=len(quiz.questions))
    fillQuestion(q, data)
    quiz.questions.append(q)
    touch(quiz)
    await db.commit()
    return await reload(db, q.id)


async def updateQuestion(db: AsyncSession, user: User, questionId: uuid.UUID, data: QuestionIn) -> Question:
    q, quiz = await getOwnedQuestion(db, user, questionId)
    await checkMedia(db, user, data.mediaId)
    fillQuestion(q, data)
    touch(quiz)
    await db.commit()
    return await reload(db, q.id)


async def deleteQuestion(db: AsyncSession, user: User, questionId: uuid.UUID) -> None:
    q, quiz = await getOwnedQuestion(db, user, questionId)
    quiz.questions.remove(q)
    for i, other in enumerate(quiz.questions):
        other.position = i
    touch(quiz)
    await db.commit()


# kopia pytania wstawiana zaraz za oryginalem
async def duplicateQuestion(db: AsyncSession, user: User, questionId: uuid.UUID) -> Question:
    q, quiz = await getOwnedQuestion(db, user, questionId)
    copy = Question(quizId=q.quizId, origin=q.origin, sourceQuote=q.sourceQuote, position=0)
    copy.type, copy.text, copy.explanation, copy.difficulty = q.type, q.text, q.explanation, q.difficulty
    copy.timeLimitS, copy.points, copy.category, copy.mediaId = q.timeLimitS, q.points, q.category, q.mediaId
    copy.options = [AnswerOption(position=o.position, text=o.text, isCorrect=o.isCorrect) for o in q.options]
    if q.openAnswer:
        oa = q.openAnswer
        copy.openAnswer = OpenAnswer(
            accepted=list(oa.accepted),
            fuzzyThreshold=oa.fuzzyThreshold,
            caseSensitive=oa.caseSensitive,
            ignoreAccents=oa.ignoreAccents,
        )
    quiz.questions.insert(quiz.questions.index(q) + 1, copy)
    for i, other in enumerate(quiz.questions):
        other.position = i
    touch(quiz)
    await db.commit()
    return await reload(db, copy.id)


# nowa kolejnosc pytan: lista musi zawierac dokladnie wszystkie pytania quizu
async def reorder(db: AsyncSession, user: User, quizId: uuid.UUID, ids: list[uuid.UUID]) -> Quiz:
    quiz = await getOwned(db, user, quizId)
    byId = {q.id: q for q in quiz.questions}
    if len(ids) != len(byId) or set(ids) != set(byId):
        raise HTTPException(400, "invalid_order")
    for i, qid in enumerate(ids):
        byId[qid].position = i
    touch(quiz)
    await db.commit()
    await db.refresh(quiz, ["questions"])
    return quiz


async def reload(db: AsyncSession, questionId: uuid.UUID) -> Question:
    db.expire_all()
    return await db.get(Question, questionId)
