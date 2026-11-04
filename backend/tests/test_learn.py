from tests.helpers import registerAndLogin
from tests.test_quizzes import OPEN, SINGLE, TF, addQ, newQuiz


async def quizWith(client, *bodies, **extra):
    quiz = await newQuiz(client, **extra)
    for b in bodies:
        assert (await addQ(client, quiz["id"], b)).status_code == 201
    return quiz


async def start(client, quizId, token=None):
    res = await client.post("/api/learn/sessions", json={"quizId": quizId, "token": token})
    assert res.status_code == 201, res.text
    return res.json()


async def nextQ(client, sid):
    res = await client.get(f"/api/learn/sessions/{sid}/next")
    assert res.status_code == 200, res.text
    return res.json()


# pelna odpowiedz z quizu wlasciciela (zeby znac poprawne odpowiedzi w tescie)
async def fullQuestions(client, quizId):
    quiz = (await client.get(f"/api/quizzes/{quizId}")).json()
    return {q["id"]: q for q in quiz["questions"]}


def goodAnswer(full):
    if full["type"] == "open":
        return {"odp": full["accepted"][0]}
    # opcje w API maja id (tez w widoku wlasciciela)
    return {"optionIds": [o["id"] for o in full["options"] if o["isCorrect"]]}


def badAnswer(full):
    if full["type"] == "open":
        return {"odp": "zupelnie nie to"}
    return {"optionIds": [o["id"] for o in full["options"] if not o["isCorrect"]][:1]}


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@ Sesja @@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_question_hides_answers_and_feedback_explains(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await quizWith(client, {**SINGLE, "explanation": "Fe od ferrum."})
    s = await start(client, quiz["id"])
    assert s["stats"]["boxes"] == [1, 0, 0, 0, 0, 0]
    q = (await nextQ(client, s["id"]))["question"]
    assert q["box"] is None and "isCorrect" not in str(q) and "explanation" not in q
    full = (await fullQuestions(client, quiz["id"]))[q["id"]]

    res = await client.post(
        f"/api/learn/sessions/{s['id']}/answer", json={"questionId": q["id"], **badAnswer(full)}
    )
    out = res.json()
    assert out["correct"] is False and out["box"] == 1 and out["prevBox"] is None
    assert out["explanation"] == "Fe od ferrum."
    assert out["correctOptionIds"] == [o["id"] for o in full["options"] if o["isCorrect"]]
    assert out["stats"]["boxes"] == [0, 1, 0, 0, 0, 0]


async def test_good_answers_move_boxes_and_open_is_checked_on_server(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await quizWith(client, OPEN)
    s = await start(client, quiz["id"])
    for expected in (1, 2, 3):
        q = (await nextQ(client, s["id"]))["question"]
        out = (
            await client.post(
                f"/api/learn/sessions/{s['id']}/answer", json={"questionId": q["id"], "odp": "warszawa"}
            )
        ).json()
        assert out["correct"] and out["box"] == expected and out["accepted"] == ["Warszawa"]
    assert out["answered"] == 3 and out["correctCount"] == 3


async def test_same_question_until_answered_and_only_current_accepted(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await quizWith(client, SINGLE, TF, OPEN)
    s = await start(client, quiz["id"])
    q1 = (await nextQ(client, s["id"]))["question"]
    assert (await nextQ(client, s["id"]))["question"]["id"] == q1["id"]
    other = next(i for i in await fullQuestions(client, quiz["id"]) if i != q1["id"])
    res = await client.post(f"/api/learn/sessions/{s['id']}/answer", json={"questionId": other, "odp": "x"})
    assert res.status_code == 409 and res.json()["detail"] == "not_current_question"


async def test_progress_survives_sessions_and_can_be_reset(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await quizWith(client, TF)
    full = await fullQuestions(client, quiz["id"])
    for _ in range(2):
        s = await start(client, quiz["id"])
        q = (await nextQ(client, s["id"]))["question"]
        await client.post(
            f"/api/learn/sessions/{s['id']}/answer", json={"questionId": q["id"], **goodAnswer(full[q["id"]])}
        )
        ended = (await client.post(f"/api/learn/sessions/{s['id']}/end")).json()
        assert ended["endedAt"] and ended["answered"] == 1
    # druga sesja zaczela od pudelka 1, wiec teraz pytanie jest w pudelku 2
    stats = (await client.get(f"/api/learn/quizzes/{quiz['id']}/progress")).json()
    assert stats["boxes"] == [0, 0, 1, 0, 0, 0]
    s = await start(client, quiz["id"])
    assert (await nextQ(client, s["id"]))["question"]["box"] == 2
    # zakonczona sesja nie przyjmuje odpowiedzi
    assert (await client.get(f"/api/learn/sessions/{ended['id']}/next")).status_code == 409

    assert (await client.delete(f"/api/learn/quizzes/{quiz['id']}/progress")).status_code == 204
    stats = (await client.get(f"/api/learn/quizzes/{quiz['id']}/progress")).json()
    assert stats["boxes"] == [1, 0, 0, 0, 0, 0] and stats["masteredPct"] == 0


async def test_mastery_counts_boxes_four_and_five(client, outbox):
    await registerAndLogin(client, outbox)
    quiz = await quizWith(client, OPEN, {**OPEN, "text": "Stolica Francji?", "accepted": ["Paryż"]})
    s = await start(client, quiz["id"])
    full = await fullQuestions(client, quiz["id"])
    for _ in range(8):
        q = (await nextQ(client, s["id"]))["question"]
        out = (
            await client.post(
                f"/api/learn/sessions/{s['id']}/answer",
                json={"questionId": q["id"], **goodAnswer(full[q["id"]])},
            )
        ).json()
    assert out["stats"]["boxes"] == [0, 0, 0, 0, 2, 0]
    assert out["stats"]["mastered"] == 2 and out["stats"]["masteredPct"] == 100


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@ Dostep @@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


async def test_access_rules(client, other, outbox):
    await registerAndLogin(client, outbox)
    private = await quizWith(client, SINGLE)
    unlisted = await quizWith(client, SINGLE, visibility="unlisted")
    public = await quizWith(client, SINGLE, visibility="public")
    empty = await newQuiz(client)
    assert (await client.post("/api/learn/sessions", json={"quizId": empty["id"]})).status_code == 409
    mine = await start(client, private["id"])

    await registerAndLogin(other, outbox, email="bartek@example.com", username="bartek")
    assert (await other.post("/api/learn/sessions", json={"quizId": private["id"]})).status_code == 404
    assert (await other.post("/api/learn/sessions", json={"quizId": unlisted["id"]})).status_code == 404
    await start(other, unlisted["id"], unlisted["shareToken"])
    await start(other, public["id"])
    # cudza sesja nie istnieje dla innego uzytkownika
    assert (await other.get(f"/api/learn/sessions/{mine['id']}/next")).status_code == 404


async def test_requires_login(client):
    res = await client.post("/api/learn/sessions", json={"quizId": "00000000-0000-0000-0000-000000000000"})
    assert res.status_code == 401


async def test_quiz_made_private_stops_session(client, other, outbox):
    await registerAndLogin(client, outbox)
    quiz = await quizWith(client, SINGLE, visibility="public")
    await registerAndLogin(other, outbox, email="bartek@example.com", username="bartek")
    s = await start(other, quiz["id"])
    await client.patch(f"/api/quizzes/{quiz['id']}", json={"visibility": "private"})
    assert (await other.get(f"/api/learn/sessions/{s['id']}/next")).status_code == 404
