import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import emails
from app.auth.models import EmailToken, User
from app.auth.schemas import RegisterIn
from app.auth.security import hashPassword, hashToken, newToken
from app.common import mail
from app.profile.models import Profile

# waznosc tokenow z e-maili
TOKEN_HOURS = {"verify": 24, "reset": 1}


def now() -> datetime:
    return datetime.now(UTC)


async def findUser(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower()))


async def getLocale(db: AsyncSession, userId: uuid.UUID) -> str:
    return await db.scalar(select(Profile.locale).where(Profile.userId == userId)) or "pl"


# nowy token; poprzednie tokeny tego samego typu przestaja dzialac
async def makeToken(db: AsyncSession, userId: uuid.UUID, purpose: str) -> str:
    await db.execute(
        update(EmailToken)
        .where(EmailToken.userId == userId, EmailToken.purpose == purpose, EmailToken.usedAt.is_(None))
        .values(usedAt=now())
    )
    raw, tokenHash = newToken()
    expires = now() + timedelta(hours=TOKEN_HOURS[purpose])
    db.add(EmailToken(userId=userId, purpose=purpose, tokenHash=tokenHash, expiresAt=expires))
    return raw


# zuzywa token z e-maila; zwraca uzytkownika albo 400
async def useToken(db: AsyncSession, raw: str, purpose: str) -> User:
    tok = await db.scalar(
        select(EmailToken).where(
            EmailToken.tokenHash == hashToken(raw),
            EmailToken.purpose == purpose,
            EmailToken.usedAt.is_(None),
            EmailToken.expiresAt > now(),
        )
    )
    if not tok:
        raise HTTPException(400, "invalid_token")
    tok.usedAt = now()
    return await db.get(User, tok.userId)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@ Rejestracja @@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def register(db: AsyncSession, data: RegisterIn) -> None:
    email = data.email.lower()
    existing = await findUser(db, email)
    if existing:
        # ta sama odpowiedz co przy nowym koncie; wlasciciel dostaje informacje mailem
        await mail.sendMail(email, *emails.buildMail("exists", await getLocale(db, existing.id)))
        return

    uname = data.username.lower()
    if await db.scalar(select(Profile.userId).where(Profile.username == uname)):
        raise HTTPException(409, "username_taken")

    user = User(email=email, passwordHash=hashPassword(data.password))
    db.add(user)
    await db.flush()
    db.add(
        Profile(
            userId=user.id, username=uname, displayName=data.displayName or data.username, locale=data.locale
        )
    )
    raw = await makeToken(db, user.id, "verify")
    await db.commit()
    await mail.sendMail(email, *emails.buildMail("verify", data.locale, raw))


# ponowna wysylka linku weryfikacyjnego (tylko dla niepotwierdzonych kont)
async def resendVerification(db: AsyncSession, email: str) -> None:
    user = await findUser(db, email)
    if not user or user.emailVerifiedAt:
        return
    raw = await makeToken(db, user.id, "verify")
    await db.commit()
    await mail.sendMail(user.email, *emails.buildMail("verify", await getLocale(db, user.id), raw))


async def verifyEmail(db: AsyncSession, raw: str) -> None:
    user = await useToken(db, raw, "verify")
    user.emailVerifiedAt = user.emailVerifiedAt or now()
    await db.commit()


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$ Reset hasla $$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


async def forgotPassword(db: AsyncSession, email: str) -> None:
    user = await findUser(db, email)
    if not user:
        return
    raw = await makeToken(db, user.id, "reset")
    await db.commit()
    await mail.sendMail(user.email, *emails.buildMail("reset", await getLocale(db, user.id), raw))


# ustawia nowe haslo; link z e-maila potwierdza tez adres
async def resetPassword(db: AsyncSession, raw: str, password: str) -> User:
    user = await useToken(db, raw, "reset")
    user.passwordHash = hashPassword(password)
    user.emailVerifiedAt = user.emailVerifiedAt or now()
    await db.commit()
    return user
