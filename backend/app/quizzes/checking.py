import re
import unicodedata

from rapidfuzz import fuzz

# litery, ktorych NFKD nie rozklada na litere + znak
EXTRA = str.maketrans({"ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "đ": "d", "Đ": "D", "ß": "ss"})


# usuwa znaki diakrytyczne: "Żółć" -> "Zolc"
def stripAccents(text: str) -> str:
    text = text.translate(EXTRA)
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


# ujednolica odpowiedz: spacje, kropka na koncu, wielkosc liter, polskie znaki
def normalize(text: str, caseSensitive: bool = False, ignoreAccents: bool = True) -> str:
    text = re.sub(r"\s+", " ", text).strip().rstrip(".!?").strip()
    if not caseSensitive:
        text = text.casefold()
    if ignoreAccents:
        text = stripAccents(text)
    return text


def isNumber(text: str) -> bool:
    return re.fullmatch(r"-?\d+([.,]\d+)?", text) is not None


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@ Sprawdzanie pytan otwartych @@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# czy odpowiedz gracza pasuje do ktoregos z akceptowanych wariantow
def checkOpen(
    odp: str,
    accepted: list[str],
    fuzzyThreshold: int = 85,
    caseSensitive: bool = False,
    ignoreAccents: bool = True,
) -> bool:
    given = normalize(odp, caseSensitive, ignoreAccents)
    if not given:
        return False
    for variant in accepted:
        good = normalize(variant, caseSensitive, ignoreAccents)
        if given == good:
            return True
        # liczby musza sie zgadzac dokladnie ("1984" i "1948" to rozne odpowiedzi)
        if isNumber(given) or isNumber(good):
            if given.replace(",", ".") == good.replace(",", "."):
                return True
            continue
        # literowki: podobienstwo tekstu (Levenshtein) w procentach;
        # przy rozroznianiu wielkosci liter liczy sie tylko dokladne dopasowanie
        if not caseSensitive and fuzzyThreshold < 100 and fuzz.ratio(given, good) >= fuzzyThreshold:
            return True
    return False
