from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import registry
from app.ai.registry import ModelOut
from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.db.session import getDb

router = APIRouter(prefix="/ai", tags=["ai"])


# lista modeli, ktorych uzytkownik moze uzyc do generowania
@router.get("/models")
async def models(user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)) -> list[ModelOut]:
    return await registry.availableModels(db, user)
