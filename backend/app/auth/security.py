import hashlib
import secrets

from pwdlib import PasswordHash

# argon2id z zalecanymi parametrami
hasher = PasswordHash.recommended()

# hash do porownania, gdy konto nie istnieje (ten sam czas odpowiedzi)
DUMMY_HASH = hasher.hash("brak-konta-brak-konta")


def hashPassword(password: str) -> str:
    return hasher.hash(password)


def checkPassword(password: str, passHash: str) -> bool:
    try:
        return hasher.verify(password, passHash)
    except Exception:
        return False


def hashToken(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# losowy token: surowy idzie do uzytkownika, hash do bazy
def newToken() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hashToken(raw)
