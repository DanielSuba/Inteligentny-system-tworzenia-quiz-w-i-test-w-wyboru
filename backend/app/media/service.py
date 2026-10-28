import re
import uuid
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import filetype
from fastapi import HTTPException
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.common.storage import Storage
from app.config import getSettings
from app.media.models import Media
from app.media.schemas import MediaLinkIn, MediaOut, MediaUpdate

# dozwolone typy plikow (rozpoznawane po zawartosci)
ALLOWED = {
    "image": {"image/jpeg", "image/png", "image/webp", "image/gif"},
    "audio": {
        "audio/mpeg",
        "audio/ogg",
        "audio/x-wav",
        "audio/wav",
        "audio/x-flac",
        "audio/mp4",
        "audio/webm",
    },
    "video": {"video/mp4", "video/webm", "video/ogg", "video/quicktime"},
}


def maxBytes(kind: str) -> int:
    s = getSettings()
    mb = {"image": s.mediaImageMb, "audio": s.mediaAudioMb, "video": s.mediaVideoMb}[kind]
    return mb * 1024 * 1024


def toOut(m: Media, store: Storage) -> MediaOut:
    url = store.url(m.path) if m.source == "upload" else m.url
    return MediaOut(
        id=m.id,
        kind=m.kind,
        source=m.source,
        url=url,
        youtubeId=m.youtubeId,
        embedId=m.embedId,
        startS=m.startS,
        endS=m.endS,
        mime=m.mime,
        crop=m.crop,
        displayWidth=m.displayWidth,
        hideVideo=m.hideVideo,
    )


# wyciaga id filmu z linku YouTube (watch?v=, youtu.be/, shorts/, embed/)
def youtubeId(url: str) -> tuple[str | None, int | None]:
    p = urlparse(url)
    host = (p.hostname or "").removeprefix("www.").removeprefix("m.")
    vid = None
    if host == "youtu.be":
        vid = p.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "youtube-nocookie.com", "music.youtube.com"):
        if p.path == "/watch":
            vid = parse_qs(p.query).get("v", [None])[0]
        else:
            m = re.match(r"^/(embed|shorts|live)/([^/?]+)", p.path)
            vid = m.group(2) if m else None
    start = parse_qs(p.query).get("t", [None])[0]
    startS = int(re.sub(r"\D", "", start)) if start and re.sub(r"\D", "", start) else None
    if vid and re.fullmatch(r"[\w-]{11}", vid):
        return vid, startS
    return None, None


# SoundCloud: odtwarzacz przyjmuje caly adres utworu
def isSoundcloud(url: str) -> bool:
    host = (urlparse(url).hostname or "").removeprefix("www.").removeprefix("m.")
    return host in ("soundcloud.com", "on.soundcloud.com")


# Spotify: open.spotify.com/(intl-xx/)track|episode|album|playlist/<id> -> "track/<id>"
def spotifyId(url: str) -> str | None:
    p = urlparse(url)
    if p.hostname != "open.spotify.com":
        return None
    m = re.match(r"^/(?:intl-[a-z-]+/)?(track|episode|album|playlist)/([A-Za-z0-9]{10,40})", p.path)
    return f"{m.group(1)}/{m.group(2)}" if m else None


# zapisuje media z linku; YouTube, SoundCloud i Spotify rozpoznawane automatycznie
async def addLink(db: AsyncSession, user: User, data: MediaLinkIn, store: Storage) -> MediaOut:
    if urlparse(data.url).scheme not in ("http", "https"):
        raise HTTPException(400, "invalid_url")
    vid, linkStart = youtubeId(data.url)
    m = Media(
        ownerId=user.id, kind=data.kind, source="link", url=data.url, startS=data.startS, endS=data.endS
    )
    if vid:
        # YouTube jako muzyka albo wideo; obrazem byc nie moze
        if data.kind == "image":
            raise HTTPException(400, "invalid_url")
        m.source, m.youtubeId = "youtube", vid
        m.startS = data.startS if data.startS is not None else linkStart
        # muzyka z YouTube domyslnie bez obrazu (gracz nie widzi tytulu ani teledysku)
        m.hideVideo = data.hideVideo if data.hideVideo is not None else data.kind == "audio"
    elif isSoundcloud(data.url) or spotifyId(data.url):
        if data.kind != "audio":
            raise HTTPException(400, "invalid_url")
        m.source = "soundcloud" if isSoundcloud(data.url) else "spotify"
        m.embedId = spotifyId(data.url)
    db.add(m)
    await db.commit()
    return toOut(m, store)


# zapisuje wgrany plik po sprawdzeniu typu i rozmiaru
async def addUpload(db: AsyncSession, user: User, kind: str, data: bytes, store: Storage) -> MediaOut:
    if len(data) > maxBytes(kind):
        raise HTTPException(413, "file_too_large")
    found = filetype.guess(data)
    mime = found.mime if found else None
    if mime not in ALLOWED[kind]:
        raise HTTPException(415, "invalid_file_type")
    if kind == "image":
        try:
            with Image.open(BytesIO(data)) as img:
                img.verify()
        except Exception as e:
            raise HTTPException(415, "invalid_file_type") from e

    m = Media(ownerId=user.id, kind=kind, source="upload", mime=mime, sizeBytes=len(data))
    m.path = f"media/{user.id}/{uuid.uuid4().hex}.{found.extension}"
    store.save(m.path, data)
    db.add(m)
    await db.commit()
    return toOut(m, store)


# zmienia ustawienia mediow (tylko wlasciciel)
async def update(db: AsyncSession, user: User, mediaId, data: MediaUpdate, store: Storage) -> MediaOut:
    m = await db.get(Media, mediaId)
    if not m or m.ownerId != user.id:
        raise HTTPException(404, "media_not_found")
    changes = data.model_dump(exclude_unset=True)
    if "crop" in changes and m.kind != "image":
        raise HTTPException(400, "crop_only_image")
    for field, value in changes.items():
        setattr(m, field, value)
    await db.commit()
    return toOut(m, store)
