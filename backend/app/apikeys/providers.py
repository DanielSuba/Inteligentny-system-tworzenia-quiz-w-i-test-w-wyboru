import httpx
from fastapi import HTTPException

# dostawcy, dla ktorych uzytkownik moze zapisac wlasny klucz
PROVIDERS = ("openrouter", "openai", "anthropic", "google")


# lekkie zapytanie sprawdzajace klucz (lista modeli albo informacja o kluczu)
def checkRequest(provider: str, key: str) -> tuple[str, dict, dict]:
    if provider == "openrouter":
        return "https://openrouter.ai/api/v1/key", {"Authorization": f"Bearer {key}"}, {}
    if provider == "openai":
        return "https://api.openai.com/v1/models", {"Authorization": f"Bearer {key}"}, {}
    if provider == "anthropic":
        return (
            "https://api.anthropic.com/v1/models",
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
            {},
        )
    return "https://generativelanguage.googleapis.com/v1beta/models", {"x-goog-api-key": key}, {}


# sprawdza klucz u dostawcy; zly klucz -> 400, brak polaczenia -> 502
async def testKey(provider: str, key: str) -> None:
    url, headers, params = checkRequest(provider, key)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=headers, params=params)
    except httpx.HTTPError as e:
        raise HTTPException(502, "provider_unreachable") from e
    if res.status_code in (400, 401, 403):
        raise HTTPException(400, "invalid_api_key")
    if res.status_code >= 300:
        raise HTTPException(502, "provider_unreachable")
