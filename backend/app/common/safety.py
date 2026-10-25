import logging
import re

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# typowe wzory kluczy API (OpenAI, Anthropic, OpenRouter, Google)
KEY_PATTERN = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|AIza[0-9A-Za-z_\-]{20,})")


def redact(text: str) -> str:
    return KEY_PATTERN.sub(lambda m: m.group(0)[:5] + "***", text)


# filtr loggera: maskuje klucze API w kazdym wpisie (na wypadek bledu gdziekolwiek)
class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if record.args:
            record.args = tuple(redact(str(a)) for a in record.args)
        return True


def installLogFilter() -> None:
    f = RedactFilter()
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(name)
        logger.addFilter(f)
        for h in logger.handlers:
            h.addFilter(f)


# bledy walidacji bez pola "input": API nie odsyla wpisanych hasel ani kluczy
async def validationHandler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{k: v for k, v in e.items() if k not in ("input", "ctx", "url")} for e in exc.errors()]
    return JSONResponse({"detail": jsonable_encoder(errors)}, status_code=422)
