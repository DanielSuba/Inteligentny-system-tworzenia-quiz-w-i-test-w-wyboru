import logging

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.ai import registry
from app.apikeys import providers
from app.apikeys.service import keyForUse
from app.config import getSettings
from app.db.redis import redis
from app.db.session import makeSession
from app.security.models import ApiKey
from tests.helpers import registerAndLogin
from tests.test_twofactor import enable2fa

SECRET = "sk-or-v1-SEKRETNYklucz1234567890abcdef"


@pytest.fixture(autouse=True)
def noNetwork(monkeypatch):
    # bez prawdziwych zapytan do dostawcow i LM Studio
    async def okKey(provider, key):
        return None

    async def noLocal():
        return []

    monkeypatch.setattr(providers, "testKey", okKey)
    monkeypatch.setattr(registry, "localModels", noLocal)


async def addKey(client, provider="openrouter", key=SECRET, label="mój"):
    return await client.post("/api/me/api-keys", json={"provider": provider, "key": key, "label": label})


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@ Wymagane 2FA @@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_key_requires_2fa(client, outbox):
    await registerAndLogin(client, outbox)
    res = await addKey(client)
    assert res.status_code == 403 and res.json()["detail"] == "2fa_required"


async def test_key_requires_step_up(client, outbox):
    await registerAndLogin(client, outbox)
    secret, codes = await enable2fa(client)
    created = await addKey(client)
    assert created.status_code == 201
    for key in await redis.keys("stepup:*"):
        await redis.delete(key)
    res = await client.delete(f"/api/me/api-keys/{created.json()['id']}")
    assert res.status_code == 403 and res.json()["detail"] == "step_up_required"
    await client.post("/api/me/2fa/verify", json={"code": codes[0]})
    assert (await client.delete(f"/api/me/api-keys/{created.json()['id']}")).status_code == 204


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$ Klucz nigdy nie wycieka $$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


async def test_key_never_returned_or_logged(client, outbox, caplog):
    caplog.set_level(logging.DEBUG)
    await registerAndLogin(client, outbox)
    await enable2fa(client)

    created = await addKey(client)
    assert created.status_code == 201 and created.json()["last4"] == SECRET[-4:]
    listed = await client.get("/api/me/api-keys")
    log = await client.get("/api/me/audit")
    # niepoprawne zapytanie: blad walidacji nie odsyla wpisanego klucza
    invalid = await client.post(
        "/api/me/api-keys", json={"provider": "openrouter", "key": SECRET, "label": "x" * 60}
    )
    assert invalid.status_code == 422
    for res in (created, listed, log, invalid):
        assert SECRET not in res.text
    assert SECRET not in caplog.text

    # w bazie tylko szyfrogram; odszyfrowanie dziala w miejscu uzycia
    async with makeSession() as db:
        row = await db.scalar(select(ApiKey))
        assert SECRET.encode() not in row.ciphertext
        assert await keyForUse(db, row.userId, "openrouter") == (SECRET, "user")


async def test_invalid_key_rejected(client, outbox, monkeypatch):
    async def badKey(provider, key):
        raise HTTPException(400, "invalid_api_key")

    monkeypatch.setattr(providers, "testKey", badKey)
    await registerAndLogin(client, outbox)
    await enable2fa(client)
    res = await addKey(client)
    assert res.status_code == 400 and res.json()["detail"] == "invalid_api_key"
    assert (await client.get("/api/me/api-keys")).json() == []


async def test_cannot_disable_2fa_with_keys(client, outbox):
    await registerAndLogin(client, outbox)
    secret, codes = await enable2fa(client)
    created = await addKey(client)
    res = await client.post("/api/me/2fa/disable", json={"code": codes[0]})
    assert res.status_code == 409 and res.json()["detail"] == "keys_require_2fa"
    await client.delete(f"/api/me/api-keys/{created.json()['id']}")
    assert (await client.post("/api/me/2fa/disable", json={"code": codes[1]})).status_code == 200


async def test_cannot_delete_someone_elses_key(client, other, outbox):
    await registerAndLogin(other, outbox, email="ola@example.com", username="ola")
    await enable2fa(other)
    theirs = (await addKey(other)).json()
    await registerAndLogin(client, outbox)
    await enable2fa(client)
    assert (await client.delete(f"/api/me/api-keys/{theirs['id']}")).status_code == 404


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%% Lista modeli %%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


async def test_models_depend_on_keys(client, outbox, monkeypatch):
    s = getSettings()
    for name in ("openrouterApiKey", "openaiApiKey", "anthropicApiKey", "googleApiKey"):
        monkeypatch.setattr(s, name, "")
    await registerAndLogin(client, outbox)
    assert (await client.get("/api/ai/models")).json() == []

    # klucz systemowy z .env
    monkeypatch.setattr(s, "openaiApiKey", "sk-systemowy-klucz-1234567890")
    models = (await client.get("/api/ai/models")).json()
    assert {m["provider"] for m in models} == {"openai"} and models[0]["source"] == "system"
    monkeypatch.setattr(s, "allowSystemKeys", False)
    assert (await client.get("/api/ai/models")).json() == []

    # wlasny klucz uzytkownika
    await enable2fa(client)
    await addKey(client)
    models = (await client.get("/api/ai/models")).json()
    assert {m["provider"] for m in models} == {"openrouter"} and all(m["source"] == "user" for m in models)


async def test_models_include_lmstudio(client, outbox, monkeypatch):
    async def local():
        return [
            registry.ModelOut(
                provider="lmstudio",
                id="qwen",
                name="qwen",
                context=None,
                priceIn=None,
                priceOut=None,
                source="local",
            )
        ]

    monkeypatch.setattr(registry, "localModels", local)
    for name in ("openrouterApiKey", "openaiApiKey", "anthropicApiKey", "googleApiKey"):
        monkeypatch.setattr(getSettings(), name, "")
    await registerAndLogin(client, outbox)
    assert (await client.get("/api/ai/models")).json()[0]["source"] == "local"


# filtr maskuje klucz, ale nie psuje liczb w formatach %d (log dostepu uvicorna)
def test_log_filter_keeps_numbers():
    from app.common.safety import RedactFilter

    rec = logging.LogRecord(
        "uvicorn.access", logging.INFO, "", 0, '%s - "%s" %d', ("sk-or-v1-TAJNYklucz1234", "GET /", 200), None
    )
    RedactFilter().filter(rec)
    text = rec.getMessage()
    assert text.endswith(" 200") and "TAJNY" not in text
