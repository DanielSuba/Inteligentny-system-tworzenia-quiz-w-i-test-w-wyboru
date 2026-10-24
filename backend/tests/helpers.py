import re

PASSWORD = "dobre-haslo-123"


# wyciaga token z linku w tresci e-maila
def tokenFrom(mailItem: dict) -> str:
    return re.search(r"token=([\w-]+)", mailItem["text"]).group(1)


async def register(client, outbox, email="ania@example.com", username="ania", password=PASSWORD):
    res = await client.post(
        "/api/auth/register", json={"email": email, "password": password, "username": username}
    )
    assert res.status_code == 201
    return tokenFrom(outbox[-1]) if outbox else None


# zaklada konto, potwierdza e-mail i loguje
async def registerAndLogin(client, outbox, email="ania@example.com", username="ania", password=PASSWORD):
    token = await register(client, outbox, email, username, password)
    assert (await client.post("/api/auth/verify-email", json={"token": token})).status_code == 200
    res = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()
