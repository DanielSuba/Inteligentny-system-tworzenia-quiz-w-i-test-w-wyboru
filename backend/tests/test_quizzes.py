import pytest

from tests.helpers import registerAndLogin

SINGLE = {
    "type": "single",
    "text": "Który pierwiastek ma symbol Fe?",
    "explanation": "Fe od łacińskiego ferrum.",
    "options": [
        {"text": "Fluor", "isCorrect": False},
        {"text": "Żelazo", "isCorrect": True},
        {"text": "Ołów", "isCorrect": False},
    ],
}
MULTI = {
    "type": "multi",
    "text": "Które są gazami szlachetnymi?",
    "options": [{"text": "Hel", "isCorrect": True}, {"text": "Neon", "isCorrect": True}, {"text": "Tlen"}],
}
TF = {
    "type": "true_false",
    "text": "Woda wrze w 100°C.",
    "options": [{"text": "Prawda", "isCorrect": True}, {"text": "Fałsz"}],
}
OPEN = {"type": "open", "text": "Stolica Polski?", "accepted": ["Warszawa"], "fuzzyThreshold": 85}


async def newQuiz(client, title="Chemia", **extra):
    res = await client.post("/api/quizzes", json={"title": title, **extra})
    assert res.status_code == 201
    return res.json()


async def addQ(client, quizId, body):
    return await client.post(f"/api/quizzes/{quizId}/questions", json=body)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Quizy @@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_quiz_crud(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client, tags=[" Chemia ", "chemia", "szkoła"])
    assert quiz["tags"] == ["chemia", "szkoła"] and quiz["isOwner"] and quiz["shareToken"]
    assert quiz["visibility"] == "private" and quiz["questions"] == []

    res = await client.patch(
        f"/api/quizzes/{quiz['id']}", json={"title": "Chemia 2", "visibility": "unlisted"}
    )
    assert res.json()["title"] == "Chemia 2" and res.json()["visibility"] == "unlisted"

    await newQuiz(client, title="Historia")
    lst = (await client.get("/api/quizzes")).json()
    assert [q["title"] for q in lst] == ["Chemia 2", "Historia"] or len(lst) == 2
    found = (await client.get("/api/quizzes", params={"q": "hist"})).json()
    assert [q["title"] for q in found] == ["Historia"]
    byTag = (await client.get("/api/quizzes", params={"q": "szkoła"})).json()
    assert [q["title"] for q in byTag] == ["Chemia 2"]

    assert (await client.delete(f"/api/quizzes/{quiz['id']}")).status_code == 204
    assert (await client.get(f"/api/quizzes/{quiz['id']}")).status_code == 404


async def test_question_types_saved(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client)
    for body in (SINGLE, MULTI, TF, OPEN):
        assert (await addQ(client, quiz["id"], body)).status_code == 201
    full = (await client.get(f"/api/quizzes/{quiz['id']}")).json()
    assert [q["type"] for q in full["questions"]] == ["single", "multi", "true_false", "open"]
    assert [q["position"] for q in full["questions"]] == [0, 1, 2, 3]
    assert full["questions"][3]["accepted"] == ["Warszawa"]
    assert full["questionCount"] == 4


@pytest.mark.parametrize(
    "body",
    [
        {**SINGLE, "options": [{"text": "A", "isCorrect": True}, {"text": "B", "isCorrect": True}]},
        {**SINGLE, "options": [{"text": "A"}, {"text": "B"}]},
        {**SINGLE, "options": [{"text": "A", "isCorrect": True}]},
        {**SINGLE, "options": [{"text": f"o{i}", "isCorrect": i == 0} for i in range(11)]},
        {**SINGLE, "options": [{"text": "A", "isCorrect": True}, {"text": " a "}]},
        {**MULTI, "options": [{"text": "A"}, {"text": "B"}]},
        {**TF, "options": [{"text": "Prawda", "isCorrect": True}, {"text": "Fałsz", "isCorrect": True}]},
        {**TF, "options": [{"text": "Prawda", "isCorrect": True}, {"text": "Fałsz"}, {"text": "Nie wiem"}]},
        {**OPEN, "accepted": []},
        {**OPEN, "accepted": ["  "]},
        {**OPEN, "options": [{"text": "A", "isCorrect": True}, {"text": "B"}]},
        {**SINGLE, "accepted": ["x"]},
        {**SINGLE, "text": ""},
        {**SINGLE, "timeLimitS": 2},
        {**SINGLE, "difficulty": 5},
    ],
)
async def test_question_validation(client, outbox, body):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client)
    assert (await addQ(client, quiz["id"], body)).status_code == 422


async def test_ten_options_allowed(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client)
    body = {**SINGLE, "options": [{"text": f"o{i}", "isCorrect": i == 3} for i in range(10)]}
    assert (await addQ(client, quiz["id"], body)).status_code == 201


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$ Edycja i kolejnosc pytan $$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


async def test_update_duplicate_delete_reorder(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client)
    a = (await addQ(client, quiz["id"], SINGLE)).json()
    b = (await addQ(client, quiz["id"], OPEN)).json()

    # zmiana typu pytania z wyboru na otwarte
    res = await client.put(
        f"/api/questions/{a['id']}", json={**OPEN, "text": "Symbol Fe to?", "accepted": ["żelazo"]}
    )
    assert res.status_code == 200 and res.json()["options"] == [] and res.json()["accepted"] == ["żelazo"]

    dup = (await client.post(f"/api/questions/{a['id']}/duplicate")).json()
    full = (await client.get(f"/api/quizzes/{quiz['id']}")).json()
    assert [q["id"] for q in full["questions"]] == [a["id"], dup["id"], b["id"]]
    assert dup["accepted"] == ["żelazo"]

    order = [b["id"], a["id"], dup["id"]]
    res = await client.put(f"/api/quizzes/{quiz['id']}/order", json={"ids": order})
    assert [q["id"] for q in res.json()["questions"]] == order
    bad = await client.put(f"/api/quizzes/{quiz['id']}/order", json={"ids": order[:2]})
    assert bad.status_code == 400

    assert (await client.delete(f"/api/questions/{a['id']}")).status_code == 204
    full = (await client.get(f"/api/quizzes/{quiz['id']}")).json()
    assert [q["id"] for q in full["questions"]] == [b["id"], dup["id"]]
    assert [q["position"] for q in full["questions"]] == [0, 1]


async def test_check_open_answer(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client)
    q = (await addQ(client, quiz["id"], OPEN)).json()
    ok = await client.post(f"/api/questions/{q['id']}/check", json={"odp": "warszawa"})
    assert ok.json() == {"correct": True}
    bad = await client.post(f"/api/questions/{q['id']}/check", json={"odp": "Kraków"})
    assert bad.json() == {"correct": False}


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%% Uprawnienia %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


async def test_only_owner_edits(client, other, outbox):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client, visibility="public")
    q = (await addQ(client, quiz["id"], SINGLE)).json()
    await registerAndLogin(other, outbox, email="ola@example.com", username="ola")

    # quiz publiczny mozna zobaczyc, ale nie mozna go zmienic
    seen = await other.get(f"/api/quizzes/{quiz['id']}")
    assert seen.status_code == 200 and seen.json()["isOwner"] is False and seen.json()["shareToken"] is None
    assert (await other.patch(f"/api/quizzes/{quiz['id']}", json={"title": "X"})).status_code == 403
    assert (await other.delete(f"/api/quizzes/{quiz['id']}")).status_code == 403
    assert (await addQ(other, quiz["id"], SINGLE)).status_code == 403
    assert (await other.put(f"/api/questions/{q['id']}", json=SINGLE)).status_code == 403
    assert (await other.delete(f"/api/questions/{q['id']}")).status_code == 403
    assert (await other.post(f"/api/questions/{q['id']}/duplicate")).status_code == 403
    assert (await other.put(f"/api/quizzes/{quiz['id']}/order", json={"ids": [q["id"]]})).status_code == 403
    assert (await other.get("/api/quizzes")).json() == []


async def test_private_and_shared_access(client, other, outbox):
    await registerAndLogin(client, outbox)
    quiz = await newQuiz(client)
    await registerAndLogin(other, outbox, email="ola@example.com", username="ola")
    token = quiz["shareToken"]

    # prywatny: niewidoczny ani bezposrednio, ani z linku
    assert (await other.get(f"/api/quizzes/{quiz['id']}")).status_code == 404
    assert (await other.get(f"/api/shared/{token}")).status_code == 404

    await client.patch(f"/api/quizzes/{quiz['id']}", json={"visibility": "unlisted"})
    assert (await other.get(f"/api/quizzes/{quiz['id']}")).status_code == 404
    assert (await other.get(f"/api/shared/{token}")).status_code == 200

    # nowy link uniewaznia stary
    newToken = (await client.post(f"/api/quizzes/{quiz['id']}/share-token")).json()["shareToken"]
    assert newToken != token
    assert (await other.get(f"/api/shared/{token}")).status_code == 404
    assert (await other.get(f"/api/shared/{newToken}")).status_code == 200


async def test_requires_login(client):
    assert (await client.get("/api/quizzes")).status_code == 401
    assert (await client.post("/api/quizzes", json={"title": "X"})).status_code == 401
