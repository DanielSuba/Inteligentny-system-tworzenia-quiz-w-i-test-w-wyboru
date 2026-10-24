from pathlib import Path

from app.config import getSettings

# pliki sa serwowane pod tym adresem (app.mount w main.py)
URL_PREFIX = "/api/media/"


# zapis plikow na dysku; pozniej mozna podmienic na S3/MinIO z tym samym interfejsem
class Storage:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, rel: str, data: bytes) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, rel: str) -> None:
        (self.root / rel).unlink(missing_ok=True)

    def exists(self, rel: str) -> bool:
        return (self.root / rel).is_file()

    def url(self, rel: str) -> str:
        return URL_PREFIX + rel


storage = Storage(getSettings().storageDir)


def getStorage() -> Storage:
    return storage
