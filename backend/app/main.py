from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.ai.router import router as aiRouter
from app.apikeys.router import router as keysRouter
from app.auth.router import router as authRouter
from app.common.csrf import csrfMiddleware
from app.common.health import router as healthRouter
from app.common.safety import installLogFilter, validationHandler
from app.common.storage import URL_PREFIX, getStorage
from app.config import getSettings
from app.generation.router import router as generationRouter
from app.generation.tasks import broker
from app.media.router import router as mediaRouter
from app.profile.router import router as meRouter
from app.quizzes.router import router as quizRouter
from app.sources.router import router as sourcesRouter
from app.twofactor.router import router as twofactorRouter

settings = getSettings()


# start i stop kolejki zadan razem z API
@asynccontextmanager
async def lifespan(_app: FastAPI):
    await broker.startup()
    yield
    await broker.shutdown()


app = FastAPI(title="Apocrypha API", version="0.1.0", lifespan=lifespan)

app.middleware("http")(csrfMiddleware)
app.add_exception_handler(RequestValidationError, validationHandler)
installLogFilter()

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
app.include_router(quizRouter, prefix="/api")
app.include_router(mediaRouter, prefix="/api")
app.include_router(twofactorRouter, prefix="/api")
app.include_router(keysRouter, prefix="/api")
app.include_router(aiRouter, prefix="/api")
app.include_router(sourcesRouter, prefix="/api")
app.include_router(generationRouter, prefix="/api")

# pliki uzytkownikow (avatary)
app.mount(URL_PREFIX.rstrip("/"), StaticFiles(directory=getStorage().root), name="media")
