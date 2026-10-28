import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed
from app.auth.models import User
from app.config import getSettings
from app.sources.chunking import chunkText, countTokens
from app.sources.models import SourceChunk, SourceDocument


# zapisuje material: tekst, fragmenty i (gdy LM Studio dziala) embeddingi
async def saveDocument(
    db: AsyncSession, user: User, kind: str, name: str, mime: str, text: str
) -> SourceDocument:
    tokens = countTokens(text)
    if tokens > getSettings().materialMaxTokens:
        raise HTTPException(413, "material_too_long")
    doc = SourceDocument(
        ownerId=user.id, kind=kind, name=name[:300], mime=mime, extractedText=text, tokenCount=tokens
    )
    db.add(doc)
    await db.flush()
    parts = chunkText(text)
    vectors = await embed(parts) or [None] * len(parts)
    for i, (part, vec) in enumerate(zip(parts, vectors, strict=True)):
        db.add(SourceChunk(documentId=doc.id, idx=i, text=part, tokenCount=countTokens(part), embedding=vec))
    await db.commit()
    await db.refresh(doc)
    return doc


async def chunkCount(db: AsyncSession, docId: uuid.UUID) -> int:
    return await db.scalar(
        select(func.count()).select_from(SourceChunk).where(SourceChunk.documentId == docId)
    )


# material wlasciciela albo 404
async def getOwnDocument(db: AsyncSession, user: User, docId: uuid.UUID) -> SourceDocument:
    doc = await db.get(SourceDocument, docId)
    if not doc or doc.ownerId != user.id:
        raise HTTPException(404, "document_not_found")
    return doc


async def chunksOf(db: AsyncSession, docIds: list[uuid.UUID]) -> list[SourceChunk]:
    rows = await db.scalars(
        select(SourceChunk)
        .where(SourceChunk.documentId.in_(docIds))
        .order_by(SourceChunk.documentId, SourceChunk.idx)
    )
    return list(rows.all())
