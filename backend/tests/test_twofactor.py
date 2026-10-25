import time

import pyotp

from app.db.redis import redis
from tests.helpers import PASSWORD, registerAndLogin

LOGIN = {"email": "ania@example.com", "password": PASSWORD}


# wlacza 2FA: zwraca sekret i kody zapasowe
async def enable2fa(client) -> tuple[str, list[str]]:
    setup = (await client.post("/api/me/2fa/setup")).json()
    res = await client.post("/api/me/2fa/enable", json={"code": pyotp.TOTP(setup["secret"]).now()})
    assert res.status_code == 200
    return setup["secret"], res.json()["codes"]


# kod z nastepnego 30-sekundowego okna (biezacy jest juz zuzyty przy wlaczaniu)
def nextCode(secret: str) -> str:
    return pyotp.TOTP(secret).at(time.time() + 30)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@ Wlaczanie 2FA @@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_enable_flow(client, outbox):
    await registerAndLogin(client, outbox)
    setup = (await client.post("/api/me/2fa/setup")).json()
    assert setup["qr"].startswith("data:image/svg+xml") and setup["uri"].startswith("otpauth://totp/")
    assert "Apocrypha" in setup["uri"]

    bad = await client.post("/api/me/2fa/enable", json={"code": "000000"})
    assert bad.status_code == 400 and bad.json()["detail"] == "invalid_code"

    res = await client.post("/api/me/2fa/enable", json={"code": pyotp.TOTP(setup["secret"]).now()})
    codes = res.json()["codes"]
    assert len(codes) == 10 and len(set(codes)) == 10 and all(len(c) == 9 for c in codes)

    me = (await client.get("/api/me")).json()
    assert me["twoFactorEnabled"] is True
    st = (await client.get("/api/me/2fa")).json()
    assert st == {"enabled": True, "backupCodesLeft": 10, "stepUpActive": True}
    log = (await client.get("/api/me/audit")).json()
    assert log[0]["action"] == "2fa_enabled"


# ten sam kod TOTP nie dziala drugi raz
async def test_code_replay_blocked(client, outbox):
    await registerAndLogin(client, outbox)
    setup = (await client.post("/api/me/2fa/setup")).json()
    code = pyotp.TOTP(setup["secret"]).now()
    assert (await client.post("/api/me/2fa/enable", json={"code": code})).status_code == 200
    assert (await client.post("/api/me/2fa/verify", json={"code": code})).status_code == 400


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$ Logowanie z 2FA $$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


async def test_login_with_totp_and_backup_code(client, outbox):
    await registerAndLogin(client, outbox)
    secret, codes = await enable2fa(client)
    await client.post("/api/auth/logout")

    # haslo to dopiero pierwszy krok
    res = await client.post("/api/auth/login", json=LOGIN)
    assert res.json() == {"status": "2fa_required"}
    assert "qf_session" not in client.cookies
    assert (await client.get("/api/me")).status_code == 401
    assert (await client.post("/api/auth/login/2fa", json={"code": "123456"})).status_code == 400

    ok = await client.post("/api/auth/login/2fa", json={"code": codes[0]})
    assert ok.status_code == 200 and ok.json()["twoFactorEnabled"] is True
    assert (await client.get("/api/me")).status_code == 200

    # kod zapasowy jest jednorazowy
    await client.post("/api/auth/logout")
    await client.post("/api/auth/login", json=LOGIN)
    assert (await client.post("/api/auth/login/2fa", json={"code": codes[0]})).status_code == 400
    ok = await client.post("/api/auth/login/2fa", json={"code": nextCode(secret)})
    assert ok.status_code == 200
    assert (await client.get("/api/me/2fa")).json()["backupCodesLeft"] == 9


async def test_login_2fa_limits(client, outbox):
    await registerAndLogin(client, outbox)
    secret, codes = await enable2fa(client)
    await client.post("/api/auth/logout")

    # bez pierwszego kroku nie ma drugiego
    assert (await client.post("/api/auth/login/2fa", json={"code": codes[0]})).status_code == 401
    # po 5 zlych kodach trzeba zaczac od hasla
    await client.post("/api/auth/login", json=LOGIN)
    for _ in range(5):
        await client.post("/api/auth/login/2fa", json={"code": "000000"})
    res = await client.post("/api/auth/login/2fa", json={"code": codes[1]})
    assert res.status_code == 401 and res.json()["detail"] == "2fa_expired"


async def test_disable_and_regenerate(client, outbox):
    await registerAndLogin(client, outbox)
    secret, codes = await enable2fa(client)
    new = await client.post("/api/me/2fa/backup-codes", json={"code": codes[0]})
    assert new.status_code == 200 and set(new.json()["codes"]).isdisjoint(codes)
    assert (await client.post("/api/me/2fa/disable", json={"code": "000000"})).status_code == 400
    res = await client.post("/api/me/2fa/disable", json={"code": new.json()["codes"][0]})
    assert res.status_code == 200
    assert (await client.get("/api/me")).json()["twoFactorEnabled"] is False
    # po wylaczeniu logowanie bez kodu
    await client.post("/api/auth/logout")
    assert (await client.post("/api/auth/login", json=LOGIN)).json()["email"] == "ania@example.com"


async def test_step_up_expires(client, outbox):
    await registerAndLogin(client, outbox)
    secret, codes = await enable2fa(client)
    for key in await redis.keys("stepup:*"):
        await redis.delete(key)
    assert (await client.get("/api/me/2fa")).json()["stepUpActive"] is False
    assert (await client.post("/api/me/2fa/verify", json={"code": nextCode(secret)})).status_code == 200
    assert (await client.get("/api/me/2fa")).json()["stepUpActive"] is True
