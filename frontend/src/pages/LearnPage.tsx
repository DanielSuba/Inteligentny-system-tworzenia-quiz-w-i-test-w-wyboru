import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams, useSearchParams } from "react-router";
import {
  endLearning,
  nextQuestion,
  sendAnswer,
  startLearning,
  type AnswerIn,
  type Feedback,
  type LearnSession,
  type LearnStats,
  type PlayQuestion,
} from "@/api/learn";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { BoxBar } from "@/modes/solo/BoxBar";
import { LearnFeedback } from "@/modes/solo/LearnFeedback";
import { LearnQuestion } from "@/modes/solo/LearnQuestion";
import { SessionSummary } from "@/modes/solo/SessionSummary";

// nauka solo: pytanie -> odpowiedz -> wyjasnienie i cytat -> nastepne (powtorki Leitnera)
export function LearnPage() {
  const { quizId = "" } = useParams();
  const [params] = useSearchParams();
  const token = params.get("token");
  const { t } = useTranslation("learn");
  const [session, setSession] = useState<LearnSession | null>(null);
  const [q, setQ] = useState<PlayQuestion | null>(null);
  const [stats, setStats] = useState<LearnStats | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [summary, setSummary] = useState<LearnSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [run, setRun] = useState(0); // nowa sesja po "Ucz sie dalej"
  const [turn, setTurn] = useState(0); // kolejne pokazanie pytania (czysty stan odpowiedzi)
  const started = useRef(-1);

  // start sesji i pierwsze pytanie (raz na sesje, tez w StrictMode)
  useEffect(() => {
    if (started.current === run) return;
    started.current = run;
    startLearning(quizId, token)
      .then(async (s) => {
        setSession(s);
        const n = await nextQuestion(s.id);
        setQ(n.question);
        setStats(n.stats);
      })
      .catch((e) => setError(errorText(e)));
  }, [quizId, token, run]);

  async function answer(a: AnswerIn) {
    if (!session) return;
    setBusy(true);
    try {
      const f = await sendAnswer(session.id, a);
      setFeedback(f);
      setStats(f.stats);
      setSession({ ...session, answered: f.answered, correct: f.correctCount });
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  const next = useCallback(async () => {
    if (!session) return;
    setBusy(true);
    try {
      const n = await nextQuestion(session.id);
      setFeedback(null);
      setTurn((x) => x + 1);
      setQ(n.question);
      setStats(n.stats);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }, [session]);

  async function finish() {
    if (!session) return;
    setBusy(true);
    try {
      setSummary(await endLearning(session.id));
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  function again() {
    setSession(null);
    setQ(null);
    setFeedback(null);
    setSummary(null);
    setError("");
    setRun((r) => r + 1);
  }

  // Enter po odpowiedzi = nastepne pytanie
  useEffect(() => {
    if (!feedback) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !busy) {
        e.preventDefault();
        void next();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [feedback, busy, next]);

  const back = token ? `/share/${token}` : `/quizzes`;

  if (summary) return <SessionSummary s={summary} onAgain={again} back={back} token={token} />;
  if (error && !session) return <Notice kind="error">{error}</Notice>;
  if (!session || !stats) return <p className="pixel text-mut">{t("common:loading")}</p>;

  const pct = session.answered ? Math.round((100 * session.correct) / session.answered) : 0;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex flex-col gap-4 border-t border-line pt-5">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <div className="mr-auto min-w-0">
            <p className="pixel uppercase text-mut">{t("title")}</p>
            <h1 className="truncate text-xl font-bold">{session.quizTitle}</h1>
          </div>
          <Button variant="secondary" onClick={finish} busy={busy}>
            {t("end")}
          </Button>
        </div>
        <p className="font-pixel text-[16px] text-mut">
          {t("sessionStats", { n: session.answered, good: session.correct, pct })}
        </p>
        <BoxBar stats={stats} />
      </header>

      {error && <Notice kind="error">{error}</Notice>}

      {q ? (
        <>
          {q.box == null && <p className="pixel uppercase text-acc">{t("newQuestion")}</p>}
          <LearnQuestion
            key={`${q.id}-${turn}`}
            q={q}
            feedback={feedback}
            busy={busy}
            onAnswer={answer}
          />
          {feedback && (
            <>
              <LearnFeedback q={q} f={feedback} />
              <Button className="self-start" onClick={next} busy={busy} autoFocus>
                {t("next")}
              </Button>
            </>
          )}
        </>
      ) : (
        <p className="text-mut">{t("empty")}</p>
      )}

      <Link to={back} className="self-start text-sm text-mut hover:text-fg">
        ← {t("back")}
      </Link>
    </div>
  );
}
