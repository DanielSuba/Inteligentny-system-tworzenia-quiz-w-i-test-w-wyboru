import io
import re

import docx
import filetype
import pymupdf
import trafilatura
from fastapi import HTTPException
from pptx import Presentation

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@ Wyciaganie tekstu z plikow @@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def pdfText(data: bytes) -> str:
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        return "\n\n".join(page.get_text() for page in doc)


def docxText(data: bytes) -> str:
    d = docx.Document(io.BytesIO(data))
    parts = [p.text for p in d.paragraphs]
    for table in d.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n\n".join(parts)


# tekst slajdow razem z notatkami prowadzacego
def pptxText(data: bytes) -> str:
    prs = Presentation(io.BytesIO(data))
    slides = []
    for n, slide in enumerate(prs.slides, 1):
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip()]
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            texts.append(slide.notes_slide.notes_text_frame.text)
        slides.append(f"[Slajd {n}]\n" + "\n".join(texts))
    return "\n\n".join(slides)


def htmlText(html: str) -> str:
    return trafilatura.extract(html, include_comments=False, include_tables=True) or ""


# porzadkuje tekst: znaki niedrukowalne, wielokrotne spacje i puste linie, dzielenie wyrazow
def clean(text: str) -> str:
    text = text.replace("\x00", "").replace("\r", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


# rozpoznaje typ po zawartosci (txt/md po nazwie) i zwraca (mime, tekst)
def extract(name: str, data: bytes) -> tuple[str, str]:
    kind = filetype.guess(data)
    mime = kind.mime if kind else ""
    try:
        if mime == "application/pdf":
            text = pdfText(data)
        elif mime == DOCX or (mime == "application/zip" and name.lower().endswith(".docx")):
            mime, text = DOCX, docxText(data)
        elif mime == PPTX or (mime == "application/zip" and name.lower().endswith(".pptx")):
            mime, text = PPTX, pptxText(data)
        elif not kind and name.lower().endswith((".txt", ".md")):
            mime, text = "text/plain", data.decode("utf-8")
        else:
            raise HTTPException(415, "unsupported_document")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(422, "document_unreadable") from e
    text = clean(text)
    if len(text) < 50:
        # np. skan bez warstwy tekstu (OCR nie jest obslugiwany)
        raise HTTPException(422, "document_empty")
    return mime, text
