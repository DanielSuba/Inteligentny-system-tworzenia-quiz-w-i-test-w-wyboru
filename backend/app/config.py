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
    mailFrom: str = "Apocrypha <no-reply@apocrypha.local>"

    # pliki uzytkownikow (avatary, pozniej materialy)
    storageDir: Path = ROOT / "storage"
    avatarMaxMb: int = 2
    mediaImageMb: int = 5
    mediaAudioMb: int = 20
    mediaVideoMb: int = 100

    sessionDays: int = 30

    # szyfrowanie kluczy API i sekretow 2FA (AES-256-GCM); stare klucze: "1:base64,2:base64"
    masterKey: str = ""
    masterKeyVersion: int = 1
    masterKeysOld: str = ""

    # klucze systemowe AI (na czas testow) i modele lokalne
    allowSystemKeys: bool = True
    systemDailyCalls: int = 50
    openrouterApiKey: str = ""
    openaiApiKey: str = ""
    anthropicApiKey: str = ""
    googleApiKey: str = ""
    lmstudioBaseUrl: str = "http://localhost:1234/v1"
    # model embeddingow w LM Studio (puste = bez embeddingow, duplikaty po podobienstwie tekstu)
    embedModel: str = "text-embedding-nomic-embed-text-v1.5"

    # materialy do generowania
    materialMaxMb: int = 20
    materialMaxTokens: int = 120000
    # kolejka zadan: "redis" (worker taskiq) albo "memory" (w tym samym procesie, testy i praca bez workera)
    taskBroker: str = "memory"

    @property
    def isProd(self) -> bool:
        return self.appEnv == "prod"


@lru_cache
def getSettings() -> Settings:
    return Settings()
