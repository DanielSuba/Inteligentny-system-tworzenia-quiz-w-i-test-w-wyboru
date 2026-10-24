# wszystkie modele w jednym miejscu, zeby Alembic i testy widzialy kazda tabele
from app.auth.models import EmailToken, User
from app.cosmetics.models import CosmeticItem, UserCosmetic
from app.media.models import Media
from app.profile.models import Profile
from app.quizzes.models import AnswerOption, OpenAnswer, Question, Quiz

__all__ = [
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
]
