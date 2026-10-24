import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import getSettings

COOKIE = "qf_csrf"
HEADER = "x-csrf-token"
SAFE = {"GET", "HEAD", "OPTIONS"}


# ochrona CSRF (double submit): zapytanie zmieniajace dane musi miec w naglowku
# te sama wartosc, co w ciasteczku qf_csrf; obca strona nie moze odczytac ciasteczka
async def csrfMiddleware(request: Request, callNext):
    token = request.cookies.get(COOKIE)
    if request.method not in SAFE and request.url.path.startswith("/api"):
        sent = request.headers.get(HEADER, "")
        if not token or not secrets.compare_digest(sent, token):
            return JSONResponse({"detail": "csrf_failed"}, status_code=403)

    response = await callNext(request)
    if not token:
        response.set_cookie(
            COOKIE,
            secrets.token_urlsafe(24),
            httponly=False,
            secure=getSettings().isProd,
            samesite="lax",
            path="/",
        )
    return response
