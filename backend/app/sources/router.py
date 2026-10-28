import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import getCurrentUser
from app.auth.models import User
from app.common.ratelimit import rateLimit
from app.config import getSettings
from app.db.session import getDb
from app.sources import fetcher, parsers, service
from app.sources.models import SourceDocument

router = APIRouter(prefix="/sources", tags=["sources"])


class DocOut(BaseModel):
    id: uuid.UUID
    kind: str
    name: str
    tokenCount: int
    chunks: int
    preview: str
    createdAt: datetime


class UrlIn(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


async def docOut(db: AsyncSession, d: SourceDocument) -> DocOut:
    return DocOut(
        id=d.id,
        kind=d.kind,
        name=d.name,
        tokenCount=d.tokenCount,
        chunks=await service.chunkCount(db, d.id),
        preview=d.extractedText[:300],
        createdAt=d.createdAt,
    )


@router.get("")
async def listDocs(user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)) -> list[DocOut]:
    rows = await db.scalars(
        select(SourceDocument)
        .where(SourceDocument.ownerId == user.id)
        .order_by(SourceDocument.createdAt.desc())
    )
    return [await docOut(db, d) for d in rows.all()]


# wgranie pliku: PDF, DOCX, PPTX, TXT, MD (bez OCR)
@router.post("/upload", status_code=201, dependencies=[Depends(rateLimit("source", 30, 3600))])
async def upload(
    file: UploadFile, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> DocOut:
    limit = getSettings().materialMaxMb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, "file_too_large")
    mime, text = parsers.extract(file.filename or "plik", data)
    return await docOut(db, await service.saveDocument(db, user, "file", file.filename or "plik", mime, text))


# strona WWW: pobranie z ochrona przed SSRF i wyciagniecie tresci artykulu
@router.post("/url", status_code=201, dependencies=[Depends(rateLimit("source", 30, 3600))])
async def addUrl(
    data: UrlIn, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> DocOut:
    finalUrl, html = await fetcher.fetchPage(data.url.strip())
    text = parsers.clean(parsers.htmlText(html)) if html else ""
    if len(text) < 50:
        raise HTTPException(422, "document_empty")
    return await docOut(db, await service.saveDocument(db, user, "url", finalUrl, "text/html", text))


@router.delete("/{docId}", status_code=204)
async def deleteDoc(
    docId: uuid.UUID, user: User = Depends(getCurrentUser), db: AsyncSession = Depends(getDb)
) -> None:
    await db.delete(await service.getOwnDocument(db, user, docId))
    await db.commit()
