import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { resetLearning, type LearnSession } from "@/api/learn";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { BoxBar } from "@/modes/solo/BoxBar";

type Props = { s: LearnSession; onAgain: () => void; back: string; token: string | null };

// podsumowanie sesji: wynik, rozklad pudelek, dalsza nauka albo reset postepu
export function SessionSummary({ s, onAgain, back, token }: Props) {
  const { t } = useTranslation("learn");
  const [stats, setStats] = useState(s.stats);
  const [msg, setMsg] = useState("");
  const pct = s.answered ? Math.round((100 * s.correct) / s.answered) : 0;
  const minutes = s.endedAt
    ? Math.max(1, Math.round((Date.parse(s.endedAt) - Date.parse(s.startedAt)) / 60000))
    : 0;

  async function reset() {
    if (!window.confirm(t("resetConfirm"))) return;
    try {
      await resetLearning(s.quizId, token);
      setStats({ ...stats, boxes: [stats.total, 0, 0, 0, 0, 0], mastered: 0, masteredPct: 0 });
      setMsg(t("resetDone"));
    } catch (e) {
      setMsg(errorText(e));
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex flex-col gap-1 border-t border-line pt-5">
        <p className="pixel uppercase text-mut">{t("summary.title")}</p>
        <h1 className="text-xl font-bold">{s.quizTitle}</h1>
      </header>
      <dl className="grid grid-cols-3 gap-3">
        {[
          [t("summary.answered"), s.answered],
          [t("summary.correct"), `${pct}%`],
          [t("summary.time"), t("summary.minutes", { n: minutes })],
        ].map(([label, value]) => (
          <div key={String(label)} className="flex flex-col gap-1 border-l-2 border-line pl-3">
            <dt className="text-sm text-mut">{label}</dt>
            <dd className="font-pixel text-[24px] text-acc">{value}</dd>
          </div>
        ))}
      </dl>
      <BoxBar stats={stats} />
      {msg && <Notice kind="info">{msg}</Notice>}
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={onAgain}>{t("summary.again")}</Button>
        <Link to={back} className="text-sm text-mut hover:text-fg">
          {t("back")}
        </Link>
        <Button variant="ghost" className="ml-auto" onClick={reset}>
          {t("reset")}
        </Button>
      </div>
    </div>
  );
}
