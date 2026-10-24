import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import getSettings

log = logging.getLogger(__name__)


# wysyla zwykly e-mail tekstowy; blad wysylki nie przerywa zapytania
async def sendMail(to: str, subject: str, text: str) -> None:
    s = getSettings()
    msg = EmailMessage()
    msg["From"] = s.mailFrom
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    try:
        await aiosmtplib.send(msg, hostname=s.smtpHost, port=s.smtpPort)
    except Exception:
        log.exception("Nie udalo sie wyslac e-maila do %s", to)
