from app.auth.models import User
from app.common.storage import Storage
from app.media.service import toOut as mediaOut
from app.quizzes.models import Question, Quiz
from app.quizzes.schemas import OptionOut, QuestionOut, QuizDetail, QuizOut


# zamiana modeli z bazy na odpowiedzi API
def questionOut(q: Question, store: Storage) -> QuestionOut:
    oa = q.openAnswer
    return QuestionOut(
        id=q.id,
        position=q.position,
        type=q.type,
        text=q.text,
        explanation=q.explanation,
        difficulty=q.difficulty,
        timeLimitS=q.timeLimitS,
        points=q.points,
        category=q.category,
        origin=q.origin,
        sourceQuote=q.sourceQuote,
        media=mediaOut(q.media, store) if q.media else None,
        options=[OptionOut(id=o.id, text=o.text, isCorrect=o.isCorrect) for o in q.options],
        accepted=oa.accepted if oa else [],
        fuzzyThreshold=oa.fuzzyThreshold if oa else 85,
        caseSensitive=oa.caseSensitive if oa else False,
        ignoreAccents=oa.ignoreAccents if oa else True,
    )


def quizOut(quiz: Quiz, user: User | None, author: str, count: int, store: Storage) -> QuizOut:
    owner = user is not None and user.id == quiz.ownerId
    return QuizOut(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        language=quiz.language,
        visibility=quiz.visibility,
        tags=quiz.tags,
        shareToken=quiz.shareToken if owner else None,
        cover=mediaOut(quiz.cover, store) if quiz.cover else None,
        isOwner=owner,
        authorName=author,
        questionCount=count,
        createdAt=quiz.createdAt,
        updatedAt=quiz.updatedAt,
    )


def quizDetail(quiz: Quiz, user: User | None, author: str, store: Storage) -> QuizDetail:
    base = quizOut(quiz, user, author, len(quiz.questions), store)
    return QuizDetail(**base.model_dump(), questions=[questionOut(q, store) for q in quiz.questions])
