from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.auth.schemas import StatusOut
from app.auth.security import checkPassword, hashPassword
from app.auth.sessions import COOKIE, deleteUserSessions
from app.common.storage import Storage, getStorage
from app.config import getSettings
from app.db.redis import getRedis
from app.db.session import getDb
from app.profile import service
from app.profile.schemas import MeOut, MeUpdate, PasswordChangeIn

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
async def getMe(user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)) -> MeOut:
    return await service.getMe(db, user)


@router.patch("")
async def updateMe(
    data: MeUpdate, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> MeOut:
    return await service.updateMe(db, user, data)


# wgranie avatara: limit rozmiaru sprawdzany przed odczytem calosci
@router.post("/avatar")
async def uploadAvatar(
    file: UploadFile,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> MeOut:
    maxBytes = getSettings().avatarMaxMb * 1024 * 1024
    data = await file.read(maxBytes + 1)
    if len(data) > maxBytes:
        raise HTTPException(413, "file_too_large")
    return await service.setAvatar(db, user, data, store)


@router.delete("/avatar")
async def deleteAvatar(
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> MeOut:
    return await service.removeAvatar(db, user, store)


# zmiana hasla: wymaga obecnego hasla, wylogowuje inne urzadzenia
@router.post("/change-password")
async def changePassword(
    data: PasswordChangeIn,
    request: Request,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    redis: Redis = Depends(getRedis),
) -> StatusOut:
    if not checkPassword(data.currentPassword, user.passwordHash):
        raise HTTPException(400, "wrong_password")
    user.passwordHash = hashPassword(data.newPassword)
    await db.commit()
    await deleteUserSessions(redis, str(user.id), keepSid=request.cookies.get(COOKIE))
    return StatusOut(status="ok")
