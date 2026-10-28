from io import BytesIO

from PIL import Image

from app.media.service import youtubeId
from tests.helpers import registerAndLogin
from tests.test_quizzes import SINGLE, newQuiz


def pngBytes() -> bytes:
    out = BytesIO()
    Image.new("RGB", (64, 48), (83, 155, 245)).save(out, "PNG")
    return out.getvalue()


def test_youtube_links():
    assert youtubeId("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s") == ("dQw4w9WgXcQ", 42)
    assert youtubeId("https://youtu.be/dQw4w9WgXcQ?t=10") == ("dQw4w9WgXcQ", 10)
    assert youtubeId("https://www.youtube.com/shorts/dQw4w9WgXcQ") == ("dQw4w9WgXcQ", None)
    assert youtubeId("https://example.com/watch?v=dQw4w9WgXcQ") == (None, None)


async def test_upload_image_and_attach(client, outbox):
    await registerAndLogin(client, outbox)
    res = await client.post(
        "/api/media-items/upload", data={"kind": "image"}, files={"file": ("a.png", pngBytes(), "image/png")}
    )
    assert res.status_code == 200
    media = res.json()
    assert media["source"] == "upload" and media["mime"] == "image/png"

    # plik jest serwowany, dziala tez pobieranie fragmentu (Range)
    got = await client.get(media["url"], headers={"Range": "bytes=0-9"})
    assert got.status_code == 206 and len(got.content) == 10

    quiz = await newQuiz(client)
    q = await client.post(f"/api/quizzes/{quiz['id']}/questions", json={**SINGLE, "mediaId": media["id"]})
    assert q.status_code == 201 and q.json()["media"]["id"] == media["id"]


async def test_upload_rejects_wrong_content(client, outbox):
    await registerAndLogin(client, outbox)
    fake = await client.post(
        "/api/media-items/upload",
        data={"kind": "image"},
        files={"file": ("a.png", b"nie obraz", "image/png")},
    )
    assert fake.status_code == 415
    # obraz wyslany jako audio
    wrongKind = await client.post(
        "/api/media-items/upload", data={"kind": "audio"}, files={"file": ("a.mp3", pngBytes(), "audio/mpeg")}
    )
    assert wrongKind.status_code == 415


async def test_upload_too_large(client, outbox):
    await registerAndLogin(client, outbox)
    big = b"\x89PNG" + b"\x00" * (5 * 1024 * 1024)
    res = await client.post(
        "/api/media-items/upload", data={"kind": "image"}, files={"file": ("a.png", big, "image/png")}
    )
    assert res.status_code == 413


async def test_links(client, outbox):
    await registerAndLogin(client, outbox)
    yt = await client.post(
        "/api/media-items/link",
        json={"kind": "video", "url": "https://youtu.be/dQw4w9WgXcQ", "startS": 5, "endS": 20},
    )
    assert yt.json()["source"] == "youtube" and yt.json()["youtubeId"] == "dQw4w9WgXcQ"
    img = await client.post(
        "/api/media-items/link", json={"kind": "image", "url": "https://example.com/a.jpg"}
    )
    assert img.json()["source"] == "link" and img.json()["url"] == "https://example.com/a.jpg"

    bad = await client.post("/api/media-items/link", json={"kind": "image", "url": "javascript:alert(1)//x"})
    assert bad.status_code == 400
    badRange = await client.post(
        "/api/media-items/link",
        json={"kind": "video", "url": "https://youtu.be/dQw4w9WgXcQ", "startS": 20, "endS": 5},
    )
    assert badRange.status_code == 422


async def test_cannot_attach_someone_elses_media(client, other, outbox):
    await registerAndLogin(other, outbox, email="ola@example.com", username="ola")
    media = (
        await other.post("/api/media-items/link", json={"kind": "image", "url": "https://example.com/a.jpg"})
    ).json()
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client)
    res = await client.post(f"/api/quizzes/{quiz['id']}/questions", json={**SINGLE, "mediaId": media["id"]})
    assert res.status_code == 400 and res.json()["detail"] == "invalid_media"


# YouTube moze byc muzyka albo wideo, ale nie obrazem
async def test_youtube_as_music(client, outbox):
    await registerAndLogin(client, outbox)
    url = "https://youtu.be/dQw4w9WgXcQ"
    music = await client.post("/api/media-items/link", json={"kind": "audio", "url": url})
    assert music.json()["kind"] == "audio" and music.json()["source"] == "youtube"
    img = await client.post("/api/media-items/link", json={"kind": "image", "url": url})
    assert img.status_code == 400


def test_music_services():
    from app.media.service import isSoundcloud, spotifyId

    assert isSoundcloud("https://soundcloud.com/artysta/utwor")
    assert (
        spotifyId("https://open.spotify.com/intl-pl/track/4uLU6hMCjMI75M1A2tKUQC?si=x")
        == "track/4uLU6hMCjMI75M1A2tKUQC"
    )
    assert spotifyId("https://example.com/track/4uLU6hMCjMI75M1A2tKUQC") is None


async def test_music_links_and_media_settings(client, outbox):
    await registerAndLogin(client, outbox)
    yt = (
        await client.post(
            "/api/media-items/link", json={"kind": "audio", "url": "https://youtu.be/dQw4w9WgXcQ"}
        )
    ).json()
    assert yt["hideVideo"] is True
    vid = (
        await client.post(
            "/api/media-items/link", json={"kind": "video", "url": "https://youtu.be/dQw4w9WgXcQ"}
        )
    ).json()
    assert vid["hideVideo"] is False
    sc = await client.post(
        "/api/media-items/link", json={"kind": "audio", "url": "https://soundcloud.com/a/b"}
    )
    assert sc.json()["source"] == "soundcloud"
    sp = await client.post(
        "/api/media-items/link",
        json={"kind": "audio", "url": "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"},
    )
    assert sp.json()["source"] == "spotify" and sp.json()["embedId"] == "track/4uLU6hMCjMI75M1A2tKUQC"
    assert (
        await client.post(
            "/api/media-items/link", json={"kind": "video", "url": "https://soundcloud.com/a/b"}
        )
    ).status_code == 400

    # kadr i wielkosc obrazu, start muzyki
    img = (
        await client.post("/api/media-items/link", json={"kind": "image", "url": "https://example.com/a.jpg"})
    ).json()
    res = await client.patch(
        f"/api/media-items/{img['id']}",
        json={"crop": {"x": 10, "y": 20, "w": 50, "h": 40}, "displayWidth": 60},
    )
    assert res.json()["crop"] == {"x": 10, "y": 20, "w": 50, "h": 40} and res.json()["displayWidth"] == 60
    bad = await client.patch(
        f"/api/media-items/{img['id']}", json={"crop": {"x": 80, "y": 0, "w": 50, "h": 40}}
    )
    assert bad.status_code == 422
    assert (
        await client.patch(f"/api/media-items/{yt['id']}", json={"crop": {"x": 0, "y": 0, "w": 50, "h": 50}})
    ).status_code == 400
    res = await client.patch(
        f"/api/media-items/{yt['id']}", json={"startS": 30, "endS": 45, "hideVideo": False}
    )
    assert res.json()["startS"] == 30 and res.json()["hideVideo"] is False
