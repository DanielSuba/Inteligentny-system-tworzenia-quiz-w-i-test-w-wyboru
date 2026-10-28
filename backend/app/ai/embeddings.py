import math

import httpx

from app.config import getSettings


# embeddingi z LM Studio (API zgodne z OpenAI); brak serwera albo modelu = None
async def embed(texts: list[str]) -> list[list[float]] | None:
    s = getSettings()
    if not texts or not s.embedModel:
        return None
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                s.lmstudioBaseUrl.rstrip("/") + "/embeddings",
                json={"model": s.embedModel, "input": texts},
            )
            res.raise_for_status()
            data = res.json()["data"]
    except (httpx.HTTPError, KeyError, ValueError):
        return None
    return [d["embedding"] for d in sorted(data, key=lambda d: d["index"])]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
