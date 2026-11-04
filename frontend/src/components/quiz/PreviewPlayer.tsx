import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { checkOpenAnswer, type QuizDetail } from "@/api/quizzes";
import { AnswerButton } from "@/components/quiz/AnswerButton";
import { MediaView } from "@/components/quiz/MediaView";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";

type Props = { quiz: QuizDetail; token?: string };

// podglad quizu jako gracz: pytanie po pytaniu, bez punktacji
export function PreviewPlayer({ quiz, token }: Props) {
  const { t } = useTranslation("quiz");
  const [n, setN] = useState(0);
  const [picked, setPicked] = useState<number[]>([]);
  const [odp, setOdp] = useState("");
  const [result, setResult] = useState<boolean | null>(null);
  const [good, setGood] = useState(0);
  const [done, setDone] = useState(false);

  const total = quiz.questions.length;
  if (!total) return <p className="text-mut">{t("preview.empty")}</p>;

  if (done) {
    return (
      <div className="flex flex-col gap-4">
        <p className="font-pixel text-[24px] text-acc">{t("preview.result", { good, total })}</p>
        <Button className="self-start" onClick={() => restart()}>
          {t("preview.again")}
        </Button>
      </div>
    );
  }

  const q = quiz.questions[n];
  const revealed = result !== null;
  const correctIdx = q.options.map((o, i) => (o.isCorrect ? i : -1)).filter((i) => i >= 0);

  function restart() {
    setN(0);
    setGood(0);
    setDone(false);
    reset();
  }

  function reset() {
    setPicked([]);
    setOdp("");
    setResult(null);
  }

  function finish(ok: boolean) {
    setResult(ok);
    if (ok) setGood((g) => g + 1);
  }

  // klikniecie odpowiedzi: przy jednokrotnym wyborze od razu sprawdza
  function pick(i: number) {
    if (revealed) return;
    if (q.type === "multi") {
      setPicked((p) => (p.includes(i) ? p.filter((x) => x !== i) : [...p, i]));
    } else {
      setPicked([i]);
      finish(q.options[i].isCorrect);
    }
  }

  function checkMulti() {
    const same = picked.length === correctIdx.length && picked.every((i) => correctIdx.includes(i));
    finish(same);
  }

  // odpowiedz otwarta sprawdzana przez serwer (ta sama funkcja co w grze)
  async function checkOpen(e: FormEvent) {
    e.preventDefault();
    if (!odp.trim()) return;
    const res = await checkOpenAnswer(q.id, odp, token).catch(() => ({ correct: false }));
    finish(res.correct);
  }

  function next() {
    if (n + 1 >= total) setDone(true);
    else setN(n + 1);
    reset();
  }

  const answerText =
    q.type === "open" ? q.accepted[0] : correctIdx.map((i) => q.options[i].text).join(", ");

  return (
    <div className="flex flex-col gap-5">
      <p className="font-pixel text-[16px] text-mut">
        {t("preview.question", { n: n + 1, total })}
      </p>
      <h2 className="text-2xl font-bold text-balance">{q.text}</h2>
      {q.media && <MediaView media={q.media} />}

      {q.type === "open" ? (
        <form onSubmit={checkOpen} className="flex flex-col gap-3 sm:flex-row">
          <input
            value={odp}
            onChange={(e) => setOdp(e.target.value)}
            disabled={revealed}
            placeholder={t("preview.answer")}
            aria-label={t("preview.answer")}
            className="min-w-0 flex-1 border border-line bg-surf2 px-3 py-2 text-lg shadow-ring outline-none focus:border-acc"
          />
          {!revealed && <Button type="submit">{t("preview.check")}</Button>}
        </form>
      ) : (
        <>
          {q.type === "multi" && !revealed && (
            <p className="text-sm text-mut">{t("preview.multiHint")}</p>
          )}
          <div className={"grid gap-3 sm:grid-cols-2"}>
            {q.options.map((o, i) => (
              <AnswerButton
                key={i}
                i={i}
                text={o.text}
                picked={picked.includes(i)}
                revealed={revealed}
                good={o.isCorrect}
                onClick={() => pick(i)}
              />
            ))}
          </div>
          {q.type === "multi" && !revealed && (
            <Button className="self-start" onClick={checkMulti} disabled={!picked.length}>
              {t("preview.check")}
            </Button>
          )}
        </>
      )}

      {revealed && (
        <div className="flex flex-col gap-3">
          <Notice kind={result ? "ok" : "error"}>
            {result ? t("preview.good") : t("preview.bad")}{" "}
            {!result && t("preview.correctWas", { answer: answerText })}
            {q.explanation && <span className="mt-1 block text-mut">{q.explanation}</span>}
          </Notice>
          <Button className="self-start" onClick={next}>
            {n + 1 >= total ? t("preview.finish") : t("preview.next")}
          </Button>
        </div>
      )}
    </div>
  );
}
