# wszystkie modele w jednym miejscu, zeby Alembic i testy widzialy kazda tabele
from app.auth.models import EmailToken, User
from app.cosmetics.models import CosmeticItem, UserCosmetic
from app.profile.models import Profile

__all__ = ["CosmeticItem", "EmailToken", "Profile", "User", "UserCosmetic"]
