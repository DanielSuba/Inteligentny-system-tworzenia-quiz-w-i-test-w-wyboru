import math
import random
from dataclasses import dataclass
from datetime import datetime

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@ Stale algorytmu @@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

BOXES = 5
# waga bazowa pudelka: pudelko 1 (nieopanowane) 16 razy czesciej niz pudelko 5
BASE = {1: 16, 2: 8, 3: 4, 4: 2, 5: 1}
# pytanie niewidziane: wyzej niz pudelko 1, zeby nowe pytania szybko weszly do nauki
UNSEEN = 24
# ile ostatnich pytan nie wraca od razu
NO_REPEAT = 5
# od ktorego pudelka pytanie liczy sie jako opanowane
MASTERED_BOX = 4


# stan jednego pytania widziany przez algorytm
@dataclass
class Card:
    id: object
    box: int | None = None  # None = jeszcze niewidziane
    lastSeen: datetime | None = None


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@ Leitner @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# dobra odpowiedz: pudelko wyzej (max 5); zla: z powrotem do 1
def nextBox(box: int | None, correct: bool) -> int:
    if not correct:
        return 1
    return min(BOXES, (box or 0) + 1)


# im dawniej widziane, tym wieksza waga (log, zeby nie rosla bez konca)
def timeFactor(lastSeen: datetime, now: datetime) -> float:
    hours = max(0.0, (now - lastSeen).total_seconds() / 3600)
    return 1 + math.log1p(hours)


# waga losowania: w = base[box] * timeFactor
def weight(card: Card, now: datetime) -> float:
    if card.box is None or card.lastSeen is None:
        return UNSEEN
    return BASE[card.box] * timeFactor(card.lastSeen, now)


# losuje nastepne pytanie z wagami, bez ostatnich NO_REPEAT pokazanych
def pick(cards: list[Card], recent: list, now: datetime, rng: random.Random | None = None) -> Card | None:
    if not cards:
        return None
    rng = rng or random.Random()
    # przy malym quizie okno musi zostawic co najmniej jedno pytanie
    window = min(NO_REPEAT, len(cards) - 1)
    blocked = set(recent[-window:]) if window > 0 else set()
    pool = [c for c in cards if c.id not in blocked] or cards
    weights = [weight(c, now) for c in pool]
    return rng.choices(pool, weights=weights, k=1)[0]


# dopisuje pytanie do historii, trzyma tylko tyle, ile potrzeba
def remember(recent: list, cardId) -> list:
    return [*[r for r in recent if r != cardId], cardId][-NO_REPEAT:]
