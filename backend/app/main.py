from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as authRouter
from app.common.csrf import csrfMiddleware
from app.common.health import router as healthRouter
from app.common.storage import URL_PREFIX, getStorage
from app.config import getSettings
from app.profile.router import router as meRouter

settings = getSettings()

app = FastAPI(title="QuizForge API", version="0.1.0")

app.middleware("http")(csrfMiddleware)

# frontend w trybie dev chodzi przez proxy Vite, CORS jest na wypadek bezposrednich zapytan
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontendUrl],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(healthRouter, prefix="/api")
app.include_router(authRouter, prefix="/api")
app.include_router(meRouter, prefix="/api")

# pliki uzytkownikow (avatary)
app.mount(URL_PREFIX.rstrip("/"), StaticFiles(directory=getStorage().root), name="media")
