import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime

import pyotp
import segno
from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.security import hashToken
from app.common.crypto import decrypt, encrypt
from app.config import getSettings
from app.security.models import BackupCode

ISSUER = "Apocrypha"
STEP_UP_S = 300  # waznosc potwierdzenia kodem (5 min)
ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # bez mylacych znakow (0/o, 1/l/i)

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@ Sekret TOTP @@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# nowy sekret zapisany w koncie (2FA wlacza sie dopiero po potwierdzeniu kodem)
def newSecret(user: User) -> str:
    secret = pyotp.random_base32()
    user.totpKeyVersion, user.totpNonce, user.totpSecret = encrypt(secret, user.id.bytes)
    return secret


def getSecret(user: User) -> str | None:
    if not user.totpSecret:
        return None
    return decrypt(user.totpKeyVersion, user.totpNonce, user.totpSecret, user.id.bytes)


# adres otpauth:// i kod QR (SVG) do zeskanowania w aplikacji uwierzytelniajacej
def qrFor(user: User, secret: str) -> tuple[str, str]:
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=ISSUER)
    qr = segno.make(uri, error="m").svg_data_uri(scale=6, border=2, dark="#000", light="#fff")
    return uri, qr


# sprawdza kod z aplikacji; ten sam kod nie zadziala drugi raz (ochrona przed podsluchaniem)
async def checkTotp(redis: Redis, user: User, code: str) -> bool:
    secret = getSecret(user)
    if not secret or not re.fullmatch(r"\d{6}", code):
        return False
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        return False
    return bool(await redis.set(f"totp:used:{user.id}:{code}", "1", ex=90, nx=True))


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$ Kody zapasowe $$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


def normCode(code: str) -> str:
    return re.sub(r"[\s-]", "", code).lower()


def hashCode(code: str) -> str:
    key = getSettings().secretKey.encode()
    return hmac.new(key, normCode(code).encode(), hashlib.sha256).hexdigest()


# 10 nowych kodow w formacie xxxx-xxxx; stare przestaja dzialac
async def newBackupCodes(db: AsyncSession, user: User) -> list[str]:
    await db.execute(delete(BackupCode).where(BackupCode.userId == user.id))
    codes = []
    for _ in range(10):
        raw = "".join(secrets.choice(ALPHABET) for _ in range(8))
        codes.append(f"{raw[:4]}-{raw[4:]}")
        db.add(BackupCode(userId=user.id, codeHash=hashCode(raw)))
    return codes


async def backupLeft(db: AsyncSession, user: User) -> int:
    rows = await db.scalars(
        select(BackupCode).where(BackupCode.userId == user.id, BackupCode.usedAt.is_(None))
    )
    return len(rows.all())


async def useBackupCode(db: AsyncSession, user: User, code: str) -> bool:
    row = await db.scalar(
        select(BackupCode).where(
            BackupCode.userId == user.id,
            BackupCode.codeHash == hashCode(code),
            BackupCode.usedAt.is_(None),
        )
    )
    if not row:
        return False
    row.usedAt = datetime.now(UTC)
    return True


# kod z aplikacji (6 cyfr) albo kod zapasowy
async def checkCode(db: AsyncSession, redis: Redis, user: User, code: str) -> bool:
    code = code.strip()
    if re.fullmatch(r"\d{6}", code):
        return await checkTotp(redis, user, code)
    return await useBackupCode(db, user, code)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%% Step-up %%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# swieze potwierdzenie kodem dla danej sesji (potrzebne do zmian kluczy API)
async def grantStepUp(redis: Redis, sid: str) -> None:
    await redis.set(f"stepup:{hashToken(sid)}", "1", ex=STEP_UP_S)


async def hasStepUp(redis: Redis, sid: str | None) -> bool:
    return bool(sid) and bool(await redis.exists(f"stepup:{hashToken(sid)}"))
