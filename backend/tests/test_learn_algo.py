import random
from collections import Counter
from datetime import UTC, datetime, timedelta

from app.learn import algo
from app.learn.algo import Card

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@ Leitner @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def test_box_up_on_good_and_back_to_one_on_bad():
    assert algo.nextBox(None, True) == 1
    assert algo.nextBox(1, True) == 2
    assert algo.nextBox(5, True) == 5
    assert algo.nextBox(4, False) == 1
    assert algo.nextBox(None, False) == 1


def test_weights_favor_low_boxes_unseen_and_old():
    fresh = NOW - timedelta(minutes=1)
    w = {b: algo.weight(Card("x", b, fresh), NOW) for b in range(1, 6)}
    assert w[1] > w[2] > w[3] > w[4] > w[5]
    assert algo.weight(Card("x"), NOW) > w[1]
    # to samo pudelko: dawno widziane wazy wiecej
    old = algo.weight(Card("x", 5, NOW - timedelta(days=7)), NOW)
    assert old > w[5]


def test_no_repeat_of_recent_questions():
    cards = [Card(i) for i in range(8)]
    recent = [0, 1, 2, 3, 4]
    rng = random.Random(1)
    picked = {algo.pick(cards, recent, NOW, rng).id for _ in range(200)}
    assert picked == {5, 6, 7}


def test_small_quiz_still_gets_a_question():
    cards = [Card("a"), Card("b")]
    rng = random.Random(2)
    # przy 2 pytaniach blokowane jest tylko ostatnie
    assert {algo.pick(cards, ["a"], NOW, rng).id for _ in range(50)} == {"b"}
    assert algo.pick([Card("a")], ["a"], NOW, rng).id == "a"
    assert algo.pick([], [], NOW, rng) is None


def test_remember_keeps_last_n_without_duplicates():
    r = []
    for i in [1, 2, 3, 2, 4, 5, 6, 7]:
        r = algo.remember(r, i)
    assert r == [3, 2, 4, 5, 6, 7][-algo.NO_REPEAT :]
    assert len(r) == algo.NO_REPEAT


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@ Symulacja @@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# uczen zawsze zna pytania A, nigdy nie zna B: B ma wracac istotnie czesciej
def test_simulation_unknown_questions_come_back_more_often():
    rng = random.Random(42)
    known = [f"A{i}" for i in range(6)]
    unknown = [f"B{i}" for i in range(6)]
    cards = {c: Card(c) for c in known + unknown}
    recent, shown, now = [], Counter(), NOW
    for _ in range(600):
        c = algo.pick(list(cards.values()), recent, now, rng)
        ok = c.id in known
        c.box = algo.nextBox(c.box, ok)
        c.lastSeen = now
        recent = algo.remember(recent, c.id)
        shown[c.id[0]] += 1
        now += timedelta(seconds=30)
    # B co najmniej 2 razy czesciej niz A (w praktyce okolo 3-4 razy)
    assert shown["B"] >= 2 * shown["A"], shown
    # opanowane pytania nadal czasem wracaja (powtorka)
    assert shown["A"] > 0
