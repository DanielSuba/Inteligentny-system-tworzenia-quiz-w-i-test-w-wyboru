import math
import re

# ok. 3.5 znaku na token (polski i angielski); wystarczy do limitow i szacowania kosztu
CHARS_PER_TOKEN = 3.5


def countTokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


# dzieli tekst na zdania (z zachowaniem akapitow jako granic)
def sentences(text: str) -> list[str]:
    out = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if para:
            out.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip())
    return out


# fragmenty ok. `size` tokenow z nakladka `overlap` tokenow (kontekst na granicy fragmentow)
def chunkText(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    chunks, cur = [], []
    for s in sentences(text):
        # bardzo dlugie "zdanie" (np. tabela) tniemy na kawalki
        while countTokens(s) > size:
            cut = int(size * CHARS_PER_TOKEN)
            cur.append(s[:cut])
            chunks.append(" ".join(cur))
            cur, s = [], s[cut:]
        if cur and countTokens(" ".join(cur + [s])) > size:
            chunks.append(" ".join(cur))
            tail, budget = [], overlap
            for prev in reversed(cur):
                budget -= countTokens(prev)
                if budget < 0:
                    break
                tail.insert(0, prev)
            cur = tail
        cur.append(s)
    if cur:
        chunks.append(" ".join(cur))
    return chunks
