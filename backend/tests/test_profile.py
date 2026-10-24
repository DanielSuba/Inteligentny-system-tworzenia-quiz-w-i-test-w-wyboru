from io import BytesIO

from PIL import Image

from app.common.storage import getStorage
from tests.helpers import PASSWORD, registerAndLogin


def pngBytes(w=400, h=300) -> bytes:
    out = BytesIO()
    Image.new("RGB", (w, h), (240, 136, 62)).save(out, "PNG")
    return out.getvalue()


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Profil @@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_update_profile(client, outbox):
    await registerAndLogin(client, outbox)
    body = {
        "displayName": "Ania K.",
        "bio": "Lubię chemię",
        "locale": "en",
        "palette": "rubin",
        "username": "ania_k",
    }
    res = await client.patch("/api/me", json=body)
    assert res.status_code == 200
    me = res.json()
    assert me["displayName"] == "Ania K." and me["palette"] == "rubin" and me["locale"] == "en"
    assert me["username"] == "ania_k"


async def test_update_profile_validation(client, outbox):
    await registerAndLogin(client, outbox)
    assert (await client.patch("/api/me", json={"palette": "neon"})).status_code == 422
    assert (await client.patch("/api/me", json={"locale": "de"})).status_code == 422
    assert (await client.patch("/api/me", json={"bio": "x" * 301})).status_code == 422


async def test_update_username_taken(client, other, outbox):
    await registerAndLogin(other, outbox, email="ola@example.com", username="ola")
    await registerAndLogin(client, outbox)
    res = await client.patch("/api/me", json={"username": "OLA"})
    assert res.status_code == 409 and res.json()["detail"] == "username_taken"


async def test_profile_requires_login(client):
    assert (await client.patch("/api/me", json={"bio": "x"})).status_code == 401


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$ Avatar $$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


async def test_avatar_upload_and_delete(client, outbox):
    await registerAndLogin(client, outbox)
    res = await client.post("/api/me/avatar", files={"file": ("a.png", pngBytes(), "image/png")})
    assert res.status_code == 200
    url = res.json()["avatarUrl"]
    assert url.startswith("/api/media/avatars/") and url.endswith(".webp")

    rel = url.removeprefix("/api/media/")
    assert getStorage().exists(rel)
    with Image.open(getStorage().root / rel) as img:
        assert img.size == (256, 256)
    assert (await client.get(url)).status_code == 200

    res = await client.delete("/api/me/avatar")
    assert res.json()["avatarUrl"] is None and not getStorage().exists(rel)


async def test_avatar_rejects_fake_image(client, outbox):
    await registerAndLogin(client, outbox)
    # rozszerzenie i typ udaja obraz, ale tresc nim nie jest
    res = await client.post("/api/me/avatar", files={"file": ("a.png", b"to nie jest obraz", "image/png")})
    assert res.status_code == 415 and res.json()["detail"] == "invalid_image"


async def test_avatar_too_large(client, outbox):
    await registerAndLogin(client, outbox)
    big = b"\x00" * (2 * 1024 * 1024 + 10)
    res = await client.post("/api/me/avatar", files={"file": ("a.png", big, "image/png")})
    assert res.status_code == 413


# ########################################
# ############# Zmiana hasla #############
# ########################################


async def test_change_password(client, other, outbox):
    await registerAndLogin(client, outbox)
    res = await other.post("/api/auth/login", json={"email": "ania@example.com", "password": PASSWORD})
    assert res.status_code == 200

    bad = await client.post(
        "/api/me/change-password", json={"currentPassword": "zle-haslo-1", "newPassword": "nowe-haslo-456"}
    )
    assert bad.status_code == 400 and bad.json()["detail"] == "wrong_password"

    ok = await client.post(
        "/api/me/change-password", json={"currentPassword": PASSWORD, "newPassword": "nowe-haslo-456"}
    )
    assert ok.status_code == 200
    # to urzadzenie zostaje zalogowane, drugie zostaje wylogowane
    assert (await client.get("/api/me")).status_code == 200
    assert (await other.get("/api/me")).status_code == 401
