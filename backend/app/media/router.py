from typing import Literal

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.common.storage import Storage, getStorage
from app.db.session import getDb
from app.media import service
from app.media.schemas import MediaLinkIn, MediaOut

router = APIRouter(prefix="/media-items", tags=["media"])


@router.post("/link")
async def addLink(
    data: MediaLinkIn,
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> MediaOut:
    return await service.addLink(db, user, data, store)


# plik czytany kawalkami: przerywamy, gdy przekroczy limit dla danego typu
@router.post("/upload")
async def upload(
    file: UploadFile,
    kind: Literal["image", "audio", "video"] = Form(),
    user: User = Depends(getCurrentUser),
    db: AsyncSession = Depends(getDb),
    store: Storage = Depends(getStorage),
) -> MediaOut:
    limit = service.maxBytes(kind)
    chunks, size = [], 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > limit:
            raise HTTPException(413, "file_too_large")
        chunks.append(chunk)
    return await service.addUpload(db, user, kind, b"".join(chunks), store)
