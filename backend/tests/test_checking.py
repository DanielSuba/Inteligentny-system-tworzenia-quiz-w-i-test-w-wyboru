from app.quizzes.checking import checkOpen, normalize

# testy funkcji sprawdzajacej odpowiedzi otwarte (bez bazy)


def test_exact_and_case():
    assert checkOpen("Warszawa", ["Warszawa"])
    assert checkOpen("  warszawa. ", ["Warszawa"])
    assert not checkOpen("warszawa", ["Warszawa"], caseSensitive=True)
    assert checkOpen("Warszawa", ["Warszawa"], caseSensitive=True)


def test_polish_letters():
    assert checkOpen("zelazo", ["Żelazo"])
    assert checkOpen("Łódź", ["lodz"])
    assert not checkOpen("zelazo", ["Żelazo"], ignoreAccents=False, fuzzyThreshold=100)
    assert normalize("Zażółć  GĘŚLĄ jaźń") == "zazolc gesla jazn"


def test_typos():
    assert checkOpen("Mickiewic", ["Adam Mickiewicz", "Mickiewicz"])
    assert checkOpen("Kopernk", ["Kopernik"])
    assert not checkOpen("Słowacki", ["Mickiewicz"])
    # prog 100 = tylko dokladne dopasowanie
    assert not checkOpen("Kopernk", ["Kopernik"], fuzzyThreshold=100)


def test_variants():
    assert checkOpen("H2O", ["woda", "H2O", "tlenek wodoru"])
    assert checkOpen("tlenek wodoru", ["woda", "H2O", "tlenek wodoru"])


def test_numbers_must_match_exactly():
    assert checkOpen("1984", ["1984"])
    assert not checkOpen("1948", ["1984"])
    assert checkOpen("3,14", ["3.14"])
    assert not checkOpen("6", ["8"])


def test_empty_answer():
    assert not checkOpen("   ", ["cokolwiek"])
    assert not checkOpen("", [""])
