import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router";
import { createQuiz, listQuizzes, type Quiz, type Visibility } from "@/api/quizzes";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { cn } from "@/lib/utils";

const filters: ("" | Visibility)[] = ["", "private", "unlisted", "public", "friends"];

// "Moje quizy": lista, szukanie, filtr widocznosci, nowy quiz
export function QuizzesPage() {
  const { t, i18n } = useTranslation("quiz");
  const navigate = useNavigate();
  const [quizzes, setQuizzes] = useState<Quiz[] | null>(null);
  const [q, setQ] = useState("");
  const [vis, setVis] = useState<"" | Visibility>("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // pobiera liste po krotkiej przerwie w pisaniu
  useEffect(() => {
    const timer = setTimeout(() => {
      listQuizzes(q.trim(), vis)
        .then(setQuizzes)
        .catch((e) => setError(errorText(e)));
    }, 250);
    return () => clearTimeout(timer);
  }, [q, vis]);

  async function add() {
    setBusy(true);
    try {
      const quiz = await createQuiz({
        title: t("list.defaultTitle"),
        language: i18n.language as "pl" | "en",
      });
      navigate(`/quizzes/${quiz.id}/edit`);
    } catch (e) {
      setError(errorText(e));
      setBusy(false);
    }
  }

  const date = (s: string) =>
    new Intl.DateTimeFormat(i18n.language, { dateStyle: "medium" }).format(new Date(s));
  const searching = q.trim() !== "" || vis !== "";

  return (
    <section className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3 border-t border-line pt-5">
        <h1 className="pixel mr-auto uppercase">{t("list.title")}</h1>
        <Button onClick={add} busy={busy}>
          + {t("list.new")}
        </Button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("list.search")}
          aria-label={t("list.search")}
          className="min-w-0 flex-1 border border-line bg-surf2 px-3 py-2 shadow-ring outline-none placeholder:text-mut focus:border-acc"
        />
        <div role="group" aria-label={t("visibility.label")} className="flex flex-wrap gap-1">
          {filters.map((f) => (
            <button
              key={f || "all"}
              aria-pressed={vis === f}
              onClick={() => setVis(f)}
              className={cn(
                "border px-2.5 py-1.5 text-sm",
                vis === f ? "border-acc text-acc" : "border-line text-mut hover:text-fg",
              )}
            >
              {f ? t(`visibility.${f}`) : t("list.all")}
            </button>
          ))}
        </div>
      </div>

      {error && <Notice kind="error">{error}</Notice>}
      {quizzes && quizzes.length === 0 && (
        <div className="flex flex-col gap-1 py-6">
          <p>{searching ? t("list.noResults") : t("list.empty")}</p>
          {!searching && <p className="text-mut">{t("list.emptyHint")}</p>}
        </div>
      )}

      <ul className="flex flex-col">
        {quizzes?.map((quiz) => (
          <li
            key={quiz.id}
            className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-dashed border-line py-3"
          >
            <Link to={`/quizzes/${quiz.id}/edit`} className="min-w-0 flex-1 basis-60">
              <span className="block truncate font-bold hover:text-acc">{quiz.title}</span>
              <span className="text-sm text-mut">
                {t("list.questions", { count: quiz.questionCount })} ·{" "}
                {t(`visibility.${quiz.visibility}`)} ·{" "}
                {t("list.updated", { date: date(quiz.updatedAt) })}
                {quiz.tags.length > 0 && <> · {quiz.tags.map((x) => `#${x}`).join(" ")}</>}
              </span>
            </Link>
            <span className="flex gap-3 text-sm">
              <Link to={`/quizzes/${quiz.id}/edit`} className="text-acc hover:underline">
                {t("list.edit")}
              </Link>
              <Link to={`/quizzes/${quiz.id}/preview`} className="text-mut hover:text-fg">
                {t("list.preview")}
              </Link>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
