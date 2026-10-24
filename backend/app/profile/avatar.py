from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

SIZE = 256
FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}

# ochrona przed "bombami" (male pliki z ogromna rozdzielczoscia)
Image.MAX_IMAGE_PIXELS = 40_000_000


# sprawdza obraz po zawartosci (nie po nazwie) i robi kwadrat 256x256 w WebP
def processAvatar(data: bytes) -> bytes:
    try:
        with Image.open(BytesIO(data)) as probe:
            fmt = probe.format
            probe.verify()
        if fmt not in FORMATS:
            raise HTTPException(415, "invalid_image")
        with Image.open(BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img).convert("RGBA")
            img = ImageOps.fit(img, (SIZE, SIZE), Image.Resampling.LANCZOS)
            out = BytesIO()
            img.save(out, "WEBP", quality=85)
            return out.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError) as e:
        raise HTTPException(415, "invalid_image") from e
