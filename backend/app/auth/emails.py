from app.config import getSettings

# tresci e-maili w obu jezykach: (temat, tekst)
TEXTS = {
    "verify": {
        "pl": (
            "QuizForge: potwierdź adres e-mail",
            "Cześć!\n\nAby dokończyć zakładanie konta w QuizForge, otwórz link:\n{link}\n\n"
            "Link jest ważny 24 godziny. Jeśli to nie Ty zakładałeś konto, zignoruj tę wiadomość.",
        ),
        "en": (
            "QuizForge: confirm your email",
            "Hi!\n\nTo finish creating your QuizForge account, open this link:\n{link}\n\n"
            "The link is valid for 24 hours. If you didn't sign up, ignore this message.",
        ),
    },
    "reset": {
        "pl": (
            "QuizForge: reset hasła",
            "Ktoś poprosił o reset hasła do Twojego konta w QuizForge.\n\n"
            "Nowe hasło ustawisz tutaj:\n{link}\n\n"
            "Link jest ważny 1 godzinę. Jeśli to nie Ty, zignoruj tę wiadomość, hasło się nie zmieni.",
        ),
        "en": (
            "QuizForge: password reset",
            "Someone asked to reset the password for your QuizForge account.\n\n"
            "Set a new password here:\n{link}\n\n"
            "The link is valid for 1 hour. If it wasn't you, ignore this message.",
        ),
    },
    "exists": {
        "pl": (
            "QuizForge: próba założenia konta",
            "Ktoś próbował założyć konto w QuizForge na ten adres, ale konto już istnieje.\n\n"
            "Jeśli nie pamiętasz hasła, ustaw nowe: {link}",
        ),
        "en": (
            "QuizForge: sign-up attempt",
            "Someone tried to create a QuizForge account with this address, but it already exists.\n\n"
            "If you forgot your password, set a new one: {link}",
        ),
    },
}


# gotowy e-mail: (temat, tekst) w jezyku uzytkownika
def buildMail(kind: str, locale: str, token: str | None = None) -> tuple[str, str]:
    base = getSettings().frontendUrl
    links = {
        "verify": f"{base}/verify-email?token={token}",
        "reset": f"{base}/reset-password?token={token}",
        "exists": f"{base}/forgot-password",
    }
    subject, text = TEXTS[kind].get(locale, TEXTS[kind]["pl"])
    return subject, text.format(link=links[kind])
