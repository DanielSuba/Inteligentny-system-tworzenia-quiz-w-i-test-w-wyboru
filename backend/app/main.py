from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.health import router as healthRouter
from app.config import getSettings

settings = getSettings()

app = FastAPI(title="QuizForge API", version="0.1.0")

# frontend w trybie dev chodzi przez proxy Vite, CORS jest na wypadek bezposrednich zapytan
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontendUrl],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(healthRouter, prefix="/api")
