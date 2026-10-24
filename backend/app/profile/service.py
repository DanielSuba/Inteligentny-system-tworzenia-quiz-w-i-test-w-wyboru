import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.common.storage import Storage, getStorage
from app.profile.avatar import processAvatar
from app.profile.models import Profile
from app.profile.schemas import MeOut, MeUpdate


async def getProfile(db: AsyncSession, userId: uuid.UUID) -> Profile:
    return await db.scalar(select(Profile).where(Profile.userId == userId))


# sklada odpowiedz /api/me z konta i profilu
async def getMe(db: AsyncSession, user: User, prof: Profile | None = None) -> MeOut:
    prof = prof or await getProfile(db, user.id)
    store = getStorage()
    return MeOut(
        id=user.id,
        email=user.email,
        emailVerified=user.emailVerifiedAt is not None,
        role=user.role,
        username=prof.username,
        displayName=prof.displayName,
        avatarUrl=store.url(prof.avatarPath) if prof.avatarPath else None,
        bio=prof.bio,
        locale=prof.locale,
        palette=prof.palette,
    )


# zmienia tylko przeslane pola profilu
async def updateMe(db: AsyncSession, user: User, data: MeUpdate) -> MeOut:
    prof = await getProfile(db, user.id)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if "username" in changes:
        uname = changes["username"].lower()
        taken = await db.scalar(
            select(Profile.userId).where(Profile.username == uname, Profile.userId != user.id)
        )
        if taken:
            raise HTTPException(409, "username_taken")
        changes["username"] = uname
    for field, value in changes.items():
        setattr(prof, field, value)
    await db.commit()
    return await getMe(db, user, prof)


# zapisuje nowy avatar pod nowa nazwa (stary adres nie zostaje w cache przegladarki)
async def setAvatar(db: AsyncSession, user: User, data: bytes, store: Storage) -> MeOut:
    image = processAvatar(data)
    prof = await getProfile(db, user.id)
    old = prof.avatarPath
    prof.avatarPath = f"avatars/{user.id}-{uuid.uuid4().hex[:8]}.webp"
    store.save(prof.avatarPath, image)
    await db.commit()
    if old:
        store.delete(old)
    return await getMe(db, user, prof)


async def removeAvatar(db: AsyncSession, user: User, store: Storage) -> MeOut:
    prof = await getProfile(db, user.id)
    if prof.avatarPath:
        store.delete(prof.avatarPath)
        prof.avatarPath = None
        await db.commit()
    return await getMe(db, user, prof)
