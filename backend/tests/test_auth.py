from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update

from app.auth.models import EmailToken, User
from app.db.session import makeSession
from tests.helpers import PASSWORD, register, registerAndLogin, tokenFrom

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@ Rejestracja @@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_full_flow(client, outbox):
    token = await register(client, outbox)
    assert outbox[0]["to"] == "ania@example.com"
    assert "/verify-email?token=" in outbox[0]["text"]

    # przed potwierdzeniem nie mozna sie zalogowac
    res = await client.post("/api/auth/login", json={"email": "ania@example.com", "password": PASSWORD})
    assert res.status_code == 403 and res.json()["detail"] == "email_not_verified"

    assert (await client.post("/api/auth/verify-email", json={"token": token})).status_code == 200
    res = await client.post("/api/auth/login", json={"email": "ANIA@example.com", "password": PASSWORD})
    assert res.status_code == 200
    assert res.json()["username"] == "ania" and res.json()["emailVerified"] is True
    assert "qf_session" in client.cookies

    me = await client.get("/api/me")
    assert me.status_code == 200 and me.json()["email"] == "ania@example.com"

    assert (await client.post("/api/auth/logout")).status_code == 204
    assert (await client.get("/api/me")).status_code == 401


async def test_register_existing_email_same_answer(client, outbox):
    await register(client, outbox)
    res = await client.post(
        "/api/auth/register", json={"email": "ania@example.com", "password": PASSWORD, "username": "inna"}
    )
    assert res.status_code == 201 and res.json() == {"status": "check_email"}
    assert "/forgot-password" in outbox[-1]["text"]
    async with makeSession() as db:
        assert await db.scalar(select(func.count()).select_from(User)) == 1


async def test_register_username_taken(client, outbox):
    await register(client, outbox)
    res = await client.post(
        "/api/auth/register", json={"email": "ola@example.com", "password": PASSWORD, "username": "ANIA"}
    )
    assert res.status_code == 409 and res.json()["detail"] == "username_taken"


async def test_register_validation(client):
    bad = [
        {"email": "zly-email", "password": PASSWORD, "username": "ania"},
        {"email": "a@example.com", "password": "krotkie", "username": "ania"},
        {"email": "a@example.com", "password": PASSWORD, "username": "a b"},
        {"email": "a@example.com", "password": PASSWORD, "username": "ab"},
    ]
    for body in bad:
        assert (await client.post("/api/auth/register", json=body)).status_code == 422


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$ Weryfikacja e-mail $$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


async def test_verify_token_errors(client, outbox):
    token = await register(client, outbox)
    assert (await client.post("/api/auth/verify-email", json={"token": "zly"})).status_code == 400
    assert (await client.post("/api/auth/verify-email", json={"token": token})).status_code == 200
    # token jest jednorazowy
    res = await client.post("/api/auth/verify-email", json={"token": token})
    assert res.status_code == 400 and res.json()["detail"] == "invalid_token"


async def test_verify_token_expired(client, outbox):
    token = await register(client, outbox)
    async with makeSession() as db:
        await db.execute(update(EmailToken).values(expiresAt=datetime.now(UTC) - timedelta(minutes=1)))
        await db.commit()
    assert (await client.post("/api/auth/verify-email", json={"token": token})).status_code == 400


async def test_resend_verification(client, outbox):
    first = await register(client, outbox)
    res = await client.post("/api/auth/resend-verification", json={"email": "ania@example.com"})
    assert res.status_code == 200 and len(outbox) == 2
    # stary link przestaje dzialac, nowy dziala
    assert (await client.post("/api/auth/verify-email", json={"token": first})).status_code == 400
    assert (
        await client.post("/api/auth/verify-email", json={"token": tokenFrom(outbox[1])})
    ).status_code == 200


async def test_resend_unknown_email_same_answer(client, outbox):
    res = await client.post("/api/auth/resend-verification", json={"email": "nikt@example.com"})
    assert res.status_code == 200 and res.json() == {"status": "check_email"} and outbox == []


# ########################################
# ############### Logowanie ##############
# ########################################


async def test_login_wrong_password_and_unknown_email(client, outbox):
    await registerAndLogin(client, outbox)
    a = await client.post("/api/auth/login", json={"email": "ania@example.com", "password": "zle-haslo-123"})
    b = await client.post("/api/auth/login", json={"email": "nikt@example.com", "password": PASSWORD})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json() == {"detail": "invalid_credentials"}


async def test_login_rotates_session(client, outbox):
    await registerAndLogin(client, outbox)
    first = client.cookies["qf_session"]
    await client.post("/api/auth/login", json={"email": "ania@example.com", "password": PASSWORD})
    assert client.cookies["qf_session"] != first


async def test_login_rate_limit(client):
    body = {"email": "nikt@example.com", "password": PASSWORD}
    codes = [(await client.post("/api/auth/login", json=body)).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10 and codes[10] == 429


async def test_csrf_required(client):
    del client.headers["x-csrf-token"]
    res = await client.post("/api/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    assert res.status_code == 403 and res.json()["detail"] == "csrf_failed"


async def test_me_requires_login(client):
    assert (await client.get("/api/me")).status_code == 401


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%% Reset hasla %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


async def test_reset_password(client, other, outbox):
    await registerAndLogin(client, outbox)
    res = await other.post("/api/auth/forgot-password", json={"email": "ania@example.com"})
    assert res.status_code == 200
    token = tokenFrom(outbox[-1])

    new = "nowe-haslo-456"
    assert (
        await other.post("/api/auth/reset-password", json={"token": token, "password": new})
    ).status_code == 200
    # stara sesja jest wylogowana, stare haslo nie dziala, nowe dziala
    assert (await client.get("/api/me")).status_code == 401
    old = await other.post("/api/auth/login", json={"email": "ania@example.com", "password": PASSWORD})
    assert old.status_code == 401
    ok = await other.post("/api/auth/login", json={"email": "ania@example.com", "password": new})
    assert ok.status_code == 200


async def test_reset_errors(client, outbox):
    res = await client.post("/api/auth/forgot-password", json={"email": "nikt@example.com"})
    assert res.status_code == 200 and outbox == []
    bad = await client.post("/api/auth/reset-password", json={"token": "zly", "password": "nowe-haslo-456"})
    assert bad.status_code == 400
    short = await client.post("/api/auth/reset-password", json={"token": "zly", "password": "krotkie"})
    assert short.status_code == 422
