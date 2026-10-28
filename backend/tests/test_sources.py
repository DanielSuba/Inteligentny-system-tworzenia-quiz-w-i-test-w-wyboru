import io

import docx
import pymupdf
import pytest
from fastapi import HTTPException
from pptx import Presentation
from pptx.util import Inches

from app.sources import fetcher
from app.sources.chunking import chunkText, countTokens
from app.sources.parsers import extract
from tests.helpers import registerAndLogin

TEXT = (
    "Fotosynteza zachodzi w chloroplastach. Rośliny wykorzystują energię światła do przekształcenia "
    "dwutlenku węgla i wody w glukozę. Jako produkt uboczny powstaje tlen. "
)


def makePdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Fotosynteza zachodzi w chloroplastach. Ten tekst pochodzi z PDF.")
    return doc.tobytes()


def makeDocx() -> bytes:
    d = docx.Document()
    d.add_paragraph("Fotosynteza zachodzi w chloroplastach. Ten tekst pochodzi z dokumentu Word.")
    out = io.BytesIO()
    d.save(out)
    return out.getvalue()


def makePptx() -> bytes:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Fotosynteza"
    box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(6), Inches(2))
    box.text_frame.text = "Fotosynteza zachodzi w chloroplastach. Tekst ze slajdu prezentacji."
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Parsery @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@pytest.mark.parametrize(
    ("name", "make", "fragment"),
    [("a.pdf", makePdf, "z PDF"), ("a.docx", makeDocx, "dokumentu Word"), ("a.pptx", makePptx, "[Slajd 1]")],
)
def test_parsers(name, make, fragment):
    mime, text = extract(name, make())
    assert "chloroplastach" in text and fragment in text


def test_txt_and_errors():
    assert extract("notatki.md", TEXT.encode())[1].startswith("Fotosynteza")
    with pytest.raises(HTTPException) as e:
        extract("a.exe", b"MZ\x90\x00" + b"\x00" * 100)
    assert e.value.detail == "unsupported_document"
    with pytest.raises(HTTPException) as e:
        extract("a.txt", b"za malo")
    assert e.value.detail == "document_empty"


def test_chunking_sizes_and_overlap():
    text = " ".join(f"Zdanie numer {i} opisuje kolejny fakt z materiału." for i in range(400))
    chunks = chunkText(text, size=200, overlap=40)
    assert len(chunks) > 5
    assert all(countTokens(c) <= 220 for c in chunks)
    # koniec fragmentu powtarza sie na poczatku nastepnego (nakladka)
    lastSentence = chunks[0].split(". ")[-1]
    assert lastSentence.rstrip(".") in chunks[1]
    assert chunkText("Krótki tekst.") == ["Krótki tekst."]


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$ SSRF $$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://localhost:8000/api/health",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://0.0.0.0/",
        "ftp://example.com/plik",
        "file:///etc/passwd",
    ],
)
def test_ssrf_blocked(url):
    with pytest.raises(HTTPException) as e:
        fetcher.checkUrl(url)
    assert e.value.status_code == 400


def test_public_ip_allowed():
    assert fetcher.isPublic("93.184.216.34")
    assert not fetcher.isPublic("::ffff:127.0.0.1")


# przekierowanie na adres wewnetrzny tez jest blokowane (kazdy krok sprawdzany od nowa)
async def test_redirect_to_private_blocked(monkeypatch):
    checked = []

    def fakeCheck(url):
        checked.append(url)
        if "127.0.0.1" in url:
            raise HTTPException(400, "url_blocked")

    class FakeRes:
        is_redirect, status_code, headers, encoding = True, 302, {"location": "http://127.0.0.1/"}, None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(fetcher, "checkUrl", fakeCheck)
    monkeypatch.setattr(fetcher.httpx.AsyncClient, "stream", lambda self, *a, **k: FakeRes())
    with pytest.raises(HTTPException) as e:
        await fetcher.fetchPage("https://example.com/")
    assert e.value.detail == "url_blocked" and checked == ["https://example.com/", "http://127.0.0.1/"]


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%% API %%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


async def test_upload_and_url(client, other, outbox, monkeypatch):
    await registerAndLogin(client, outbox)
    res = await client.post(
        "/api/sources/upload", files={"file": ("wyklad.pdf", makePdf(), "application/pdf")}
    )
    assert res.status_code == 201 and res.json()["chunks"] == 1

    async def fakeFetch(url):
        return url, f"<html><body><article><h1>Fotosynteza</h1><p>{TEXT * 3}</p></article></body></html>"

    monkeypatch.setattr(fetcher, "fetchPage", fakeFetch)
    page = await client.post("/api/sources/url", json={"url": "https://example.com/fotosynteza"})
    assert page.status_code == 201 and page.json()["kind"] == "url"
    assert len((await client.get("/api/sources")).json()) == 2

    # cudzy material jest niewidoczny
    await registerAndLogin(other, outbox, email="ola@example.com", username="ola")
    assert (await other.get("/api/sources")).json() == []
    assert (await other.delete(f"/api/sources/{res.json()['id']}")).status_code == 404
