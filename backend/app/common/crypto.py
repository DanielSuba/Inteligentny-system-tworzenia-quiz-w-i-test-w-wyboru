import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import getSettings


class CryptoError(Exception):
    pass


# klucze glowne wedlug wersji: aktualny + stare (do odczytu danych sprzed rotacji)
def masterKeys() -> dict[int, bytes]:
    s = getSettings()
    keys = {}
    for part in filter(None, (p.strip() for p in s.masterKeysOld.split(","))):
        ver, b64 = part.split(":", 1)
        keys[int(ver)] = base64.b64decode(b64)
    if s.masterKey:
        keys[s.masterKeyVersion] = base64.b64decode(s.masterKey)
    for k in keys.values():
        if len(k) != 32:
            raise CryptoError("klucz glowny musi miec 32 bajty")
    return keys


# szyfruje tekst aktualnym kluczem; zwraca (wersja klucza, nonce, szyfrogram)
def encrypt(text: str, aad: bytes = b"") -> tuple[int, bytes, bytes]:
    s = getSettings()
    key = masterKeys().get(s.masterKeyVersion)
    if not key:
        raise CryptoError("brak MASTER_KEY w .env")
    nonce = os.urandom(12)
    return s.masterKeyVersion, nonce, AESGCM(key).encrypt(nonce, text.encode(), aad)


# odszyfrowuje; aad musi byc ten sam co przy szyfrowaniu (np. id uzytkownika)
def decrypt(version: int, nonce: bytes, data: bytes, aad: bytes = b"") -> str:
    key = masterKeys().get(version)
    if not key:
        raise CryptoError(f"brak klucza glownego w wersji {version}")
    return AESGCM(key).decrypt(nonce, data, aad).decode()
