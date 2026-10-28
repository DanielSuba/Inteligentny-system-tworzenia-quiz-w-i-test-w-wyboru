# wszystkie modele w jednym miejscu, zeby Alembic i testy widzialy kazda tabele
from app.auth.models import EmailToken, User
from app.cosmetics.models import CosmeticItem, UserCosmetic
from app.generation.models import GeneratedQuestion, GenerationJob, QuestionReview
from app.media.models import Media
from app.profile.models import Profile
from app.quizzes.models import AnswerOption, OpenAnswer, Question, Quiz
from app.security.models import ApiKey, AuditLog, BackupCode
from app.sources.models import SourceChunk, SourceDocument

__all__ = [
    "ApiKey",
    "AuditLog",
    "BackupCode",
    "AnswerOption",
    "CosmeticItem",
    "EmailToken",
    "Media",
    "OpenAnswer",
    "Profile",
    "Question",
    "Quiz",
    "User",
    "UserCosmetic",
    "GeneratedQuestion",
    "GenerationJob",
    "QuestionReview",
    "SourceChunk",
    "SourceDocument",
]
