from functools import lru_cache
from pathlib import Path

from pydantic.alias_generators import to_snake
from pydantic_settings import BaseSettings, SettingsConfigDict

# plik .env lezy w glownym folderze projektu
ROOT = Path(__file__).resolve().parents[2]


# ustawienia aplikacji czytane z .env (DATABASE_URL -> databaseUrl)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        extra="ignore",
        alias_generator=to_snake,
        populate_by_name=True,
    )

    appEnv: str = "dev"
    secretKey: str = "zmien-mnie"
    frontendUrl: str = "http://localhost:5173"

    databaseUrl: str = "postgresql+asyncpg://quizforge:quizforge@localhost:5432/quizforge"
    redisUrl: str = "redis://localhost:6379/0"

    smtpHost: str = "localhost"
    smtpPort: int = 1025
    mailFrom: str = "QuizForge <no-reply@quizforge.local>"

    # pliki uzytkownikow (avatary, pozniej materialy)
    storageDir: Path = ROOT / "storage"
    avatarMaxMb: int = 2
    mediaImageMb: int = 5
    mediaAudioMb: int = 20
    mediaVideoMb: int = 100

    sessionDays: int = 30

    @property
    def isProd(self) -> bool:
        return self.appEnv == "prod"


@lru_cache
def getSettings() -> Settings:
    return Settings()
