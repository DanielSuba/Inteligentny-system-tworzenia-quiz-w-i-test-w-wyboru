import re

from pydantic import ValidationError
from rapidfuzz import fuzz

from app.ai.embeddings import cosine
from app.quizzes.schemas import QuestionIn

GROUNDED_MIN = 90  # od tylu % podobienstwa cytat uznajemy za znaleziony w materiale
DUP_TEXT = 88  # podobienstwo tekstu pytan (bez embeddingow)
DUP_EMBED = 0.92  # podobienstwo cosinusowe embeddingow
TF_WORDS = {"prawda", "fałsz", "falsz", "true", "false"}


def norm(text: str) -> str:
    text = re.sub(r"[^\w\s]", " ", text.casefold())
    return re.sub(r"\s+", " ", text).strip()


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@ Zgodnosc ze zrodlem @@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# czy cytat z odpowiedzi modelu naprawde wystepuje w materiale (po normalizacji albo prawie doslownie)
def grounding(quote: str, material: str) -> tuple[bool, float]:
    q, m = norm(quote), norm(material)
    if len(q) < 8:
        return False, 0.0
    if q in m:
        return True, 100.0
    score = fuzz.partial_ratio(q, m)
    return score >= GROUNDED_MIN, round(score, 1)


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$ Duplikaty $$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


# zwraca tresc pytania, ktorego to jest duplikatem (embeddingi albo podobienstwo tekstu)
def findDuplicate(
    text: str, vec: list[float] | None, others: list[tuple[str, list[float] | None]]
) -> str | None:
    for other, otherVec in others:
        if vec and otherVec and cosine(vec, otherVec) >= DUP_EMBED:
            return other
        if fuzz.token_sort_ratio(norm(text), norm(other)) >= DUP_TEXT:
            return other
    return None


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%% Reguly typow pytan %%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# pytanie z modelu -> dane jak z edytora; bledy jako lista komunikatow (te same reguly co w edytorze)
def toQuestionIn(parsed: dict) -> tuple[QuestionIn | None, list[str]]:
    data = {
        "type": parsed.get("type"),
        "text": (parsed.get("question") or "")[:500],
        "explanation": (parsed.get("explanation") or "")[:1000],
        "difficulty": parsed.get("difficulty") or 2,
        "options": [
            {"text": o.get("text", "")[:200], "isCorrect": bool(o.get("isCorrect"))}
            for o in parsed.get("options", [])
        ],
        "accepted": parsed.get("acceptedAnswers", []) if parsed.get("type") == "open" else [],
    }
    if data["type"] == "open":
        data["options"] = []
    # prawda/falsz od modelu musi miec odpowiedzi "Prawda"/"Falsz" (modele czasem podaja tu zwykle opcje)
    if data["type"] == "true_false" and {norm(o["text"]) for o in data["options"]} - TF_WORDS:
        return None, ["prawda/falsz: odpowiedzi musza brzmiec Prawda i Fałsz"]
    try:
        return QuestionIn(**data), []
    except ValidationError as e:
        return None, [err["msg"].removeprefix("Value error, ") for err in e.errors()]


# tekst pytania do liczenia, jak mocno recenzent je poprawil
def asText(q: dict) -> str:
    opts = " | ".join(f"{o.get('text', '')}{'*' if o.get('isCorrect') else ''}" for o in q.get("options", []))
    acc = " | ".join(q.get("accepted", q.get("acceptedAnswers", [])))
    return f"{q.get('text', q.get('question', ''))} || {opts} || {acc} || {q.get('explanation', '')}"
