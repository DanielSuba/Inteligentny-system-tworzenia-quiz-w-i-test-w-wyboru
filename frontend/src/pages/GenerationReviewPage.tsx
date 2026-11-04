import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router";
import {
  acceptAll,
  acceptGenerated,
  getJob,
  regenerate,
  rejectGenerated,
  type Job,
} from "@/api/generation";
import type { QuestionIn } from "@/api/quizzes";
import { GeneratedCard } from "@/components/generation/GeneratedCard";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";

// recenzja pytan z jednego generowania; dopoki model pracuje, strona pyta o postep co 1,5 s
export function GenerationReviewPage() {
  const { jobId = "" } = useParams();
  const { t } = useTranslation("generate");
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const load = useCallback(
    () =>
      getJob(jobId)
        .then(setJob)
        .catch((e) => setError(errorText(e))),
    [jobId],
  );

  useEffect(() => {
    load();
  }, [load]);

  const working = job?.status === "queued" || job?.status === "running";
  useEffect(() => {
    if (!working) return;
    const timer = setInterval(load, 1500);
    return () => clearInterval(timer);
  }, [working, load]);

  // akcja na pytaniu, potem odswiezenie listy
  async function act(action: () => Promise<unknown>) {
    setError("");
    try {
      await action();
    } catch (e) {
      setError(errorText(e));
    }
    await load();
  }

  if (!job)
    return error ? (
      <Notice kind="error">{error}</Notice>
    ) : (
      <p className="pixel text-mut">{t("common:loading")}</p>
    );

  const visible = job.questions.filter((q) => q.status !== "replaced");
  const pending = visible.filter((q) => q.status === "pending");
  const accepted = visible.filter((q) => q.status === "accepted" || q.status === "edited").length;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <Link to={`/quizzes/${job.quizId}/edit`} className="text-sm text-mut hover:text-fg">
          ← {t("review.toQuiz")}
        </Link>
        <h1 className="pixel mr-auto uppercase">{t("review.title")}</h1>
      </div>

      <p className="text-sm text-mut">
        {t("review.stats", {
          model: job.model,
          calls: job.calls,
          tin: job.tokensIn,
          tout: job.tokensOut,
          s: (job.durationMs / 1000).toFixed(1),
        })}
        {job.costUsd != null && t("review.cost", { c: job.costUsd })}
      </p>

      {working && (
        <div className="flex flex-col gap-2">
          <p className="pixel text-acc">
            {job.status === "queued"
              ? t("review.queued")
              : t("review.running", { p: job.progress })}
          </p>
          <div className="flex h-2 gap-0.5">
            {Array.from({ length: 20 }, (_, i) => (
              <i key={i} className={i < job.progress / 5 ? "flex-1 bg-acc" : "flex-1 bg-surf2"} />
            ))}
          </div>
        </div>
      )}
      {job.status === "error" && (
        <Notice kind="error">
          {job.error === "interrupted"
            ? t("review.interrupted")
            : t("review.error", { e: job.error ?? "" })}
        </Notice>
      )}
      {job.status === "done" && job.error && (
        <Notice kind="info">{t("review.partial", { e: job.error })}</Notice>
      )}
      {job.status === "done" && visible.length === 0 && (
        <p className="text-mut">{t("review.empty")}</p>
      )}
      {error && <Notice kind="error">{error}</Notice>}
      {info && <Notice kind="ok">{info}</Notice>}

      {pending.length > 0 && !working && (
        <div className="flex flex-wrap items-center gap-3 border-t border-line pt-4">
          <span className="text-sm text-mut">{t("review.pending", { n: pending.length })}</span>
          <Button
            onClick={() =>
              act(async () =>
                setInfo(t("review.acceptedAll", { n: (await acceptAll(job.id)).accepted })),
              )
            }
          >
            {t("review.acceptAll")}
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              act(async () => {
                await acceptAll(job.id);
                navigate(`/learn/${job.quizId}`);
              })
            }
          >
            {t("review.acceptAllLearn")}
          </Button>
        </div>
      )}
      {job.status === "done" && pending.length === 0 && accepted > 0 && (
        <Link to={`/learn/${job.quizId}`} className="self-start text-acc hover:underline">
          {t("learn:start")}
        </Link>
      )}

      <ol className="flex flex-col">
        {visible.map((g) => (
          <GeneratedCard
            key={g.id}
            g={g}
            onAccept={(edited?: QuestionIn) => act(() => acceptGenerated(g.id, edited))}
            onReject={() => act(() => rejectGenerated(g.id))}
            onRegenerate={() => act(() => regenerate(g.id))}
          />
        ))}
      </ol>
    </div>
  );
}
