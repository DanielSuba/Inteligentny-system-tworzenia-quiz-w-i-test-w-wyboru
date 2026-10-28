import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router";
import { estimate, listSources, startJob, type JobIn, type SourceDoc } from "@/api/generation";
import { getQuiz, type QuizDetail } from "@/api/quizzes";
import { getModels, type Model } from "@/api/security";
import { GenSettings } from "@/components/generation/GenSettings";
import { MaterialsPicker } from "@/components/generation/MaterialsPicker";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { cn } from "@/lib/utils";

type Est = { tokensIn: number; tokensOut: number; costUsd: number | null };

// kreator generowania: zrodlo (material albo temat), ustawienia, szacunek kosztu, start
export function GeneratePage() {
  const { id = "" } = useParams();
  const { t } = useTranslation("generate");
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [docs, setDocs] = useState<SourceDoc[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [est, setEst] = useState<Est | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<JobIn>({
    quizId: id,
    provider: "",
    model: "",
    strategy: "few_shot",
    mode: "material",
    documentIds: [],
    topic: "",
    focus: "",
    count: 10,
    types: ["single"],
    difficulty: 0,
    language: "pl",
    temperature: 0.7,
  });

  useEffect(() => {
    Promise.all([getQuiz(id), listSources(), getModels()])
      .then(([q, d, m]) => {
        setQuiz(q);
        setDocs(d);
        setModels(m);
        setForm((f) => ({
          ...f,
          language: q.language,
          provider: m[0]?.provider ?? "",
          model: m[0]?.id ?? "",
        }));
      })
      .catch((e) => setError(errorText(e)));
  }, [id]);

  const ready =
    !!form.model &&
    (form.mode === "material" ? form.documentIds.length > 0 : form.topic.trim() !== "");

  // szacunek tokenow i kosztu odswiezany po zmianie ustawien
  useEffect(() => {
    if (!ready) return;
    const timer = setTimeout(() => {
      estimate(form)
        .then(setEst)
        .catch(() => setEst(null));
    }, 300);
    return () => clearTimeout(timer);
  }, [form, ready]);

  const patch = (p: Partial<JobIn>) => setForm((f) => ({ ...f, ...p }));

  async function start() {
    setBusy(true);
    setError("");
    try {
      const job = await startJob(form);
      navigate(`/generation/${job.id}`);
    } catch (e) {
      setError(errorText(e));
      setBusy(false);
    }
  }

  const tab = (on: boolean) =>
    cn(
      "border-b-2 px-3 py-1.5",
      on ? "border-acc text-fg" : "border-transparent text-mut hover:text-fg",
    );

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link to={`/quizzes/${id}/edit`} className="text-sm text-mut hover:text-fg">
          ← {quiz?.title ?? ""}
        </Link>
        <h1 className="pixel mr-auto uppercase">{t("title")}</h1>
      </div>

      <section className="flex flex-col gap-4 border-t border-line pt-5">
        <h2 className="pixel uppercase text-mut">{t("source.title")}</h2>
        <div className="flex gap-1 border-b border-line" role="tablist">
          <button
            role="tab"
            aria-selected={form.mode === "material"}
            className={tab(form.mode === "material")}
            onClick={() => patch({ mode: "material" })}
          >
            {t("source.material")}
          </button>
          <button
            role="tab"
            aria-selected={form.mode === "topic"}
            className={tab(form.mode === "topic")}
            onClick={() => patch({ mode: "topic" })}
          >
            {t("source.topic")}
          </button>
        </div>
        {form.mode === "material" ? (
          <>
            <MaterialsPicker
              docs={docs}
              selected={form.documentIds}
              onSelect={(documentIds) => patch({ documentIds })}
              onDocs={setDocs}
            />
            <Field
              label={t("source.focus")}
              value={form.focus}
              maxLength={300}
              onChange={(e) => patch({ focus: e.target.value })}
              hint={t("source.focusHint")}
            />
          </>
        ) : (
          <Field
            label={t("source.topicLabel")}
            value={form.topic}
            maxLength={300}
            onChange={(e) => patch({ topic: e.target.value })}
            hint={t("source.topicHint")}
          />
        )}
      </section>

      <section className="flex flex-col gap-4 border-t border-line pt-5">
        <h2 className="pixel uppercase text-mut">{t("settings.title")}</h2>
        <GenSettings form={form} models={models} onChange={patch} />
      </section>

      <section className="flex flex-col gap-3 border-t border-line pt-5">
        {ready && est && (
          <p className="text-sm text-mut">
            {t("settings.estimate", { tin: est.tokensIn, tout: est.tokensOut })} ·{" "}
            {est.costUsd === 0
              ? t("settings.free")
              : est.costUsd != null
                ? t("settings.cost", { c: est.costUsd })
                : t("settings.costUnknown")}
          </p>
        )}
        {!ready && <p className="text-sm text-mut">{t("settings.needSource")}</p>}
        {error && <Notice kind="error">{error}</Notice>}
        <Button className="self-start" onClick={start} busy={busy} disabled={!ready}>
          {t("settings.start")}
        </Button>
      </section>
    </div>
  );
}
