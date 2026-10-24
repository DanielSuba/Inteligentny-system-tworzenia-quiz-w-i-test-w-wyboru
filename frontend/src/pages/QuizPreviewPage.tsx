import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { getQuiz, getShared, type QuizDetail } from "@/api/quizzes";
import { PreviewPlayer } from "@/components/quiz/PreviewPlayer";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";

// podglad quizu: wlasny (/quizzes/:id/preview) albo z linku (/share/:token)
export function QuizPreviewPage() {
  const { id, token } = useParams();
  const { t } = useTranslation("quiz");
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = token ? getShared(token) : getQuiz(id ?? "");
    load.then(setQuiz).catch((e) => setError(errorText(e)));
  }, [id, token]);

  if (error) return <Notice kind="error">{error}</Notice>;
  if (!quiz) return <p className="pixel text-mut">{t("common:loading")}</p>;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex flex-col gap-1 border-t border-line pt-5">
        <p className="pixel uppercase text-mut">{t("preview.title")}</p>
        <h1 className="text-xl font-bold">{quiz.title}</h1>
        <p className="text-sm text-mut">
          {t("preview.author", { name: quiz.authorName })} · {t("preview.asPlayer")}
        </p>
        {quiz.isOwner && (
          <Link
            to={`/quizzes/${quiz.id}/edit`}
            className="self-start text-sm text-acc hover:underline"
          >
            {t("preview.toEditor")}
          </Link>
        )}
      </header>
      <PreviewPlayer quiz={quiz} token={token} />
    </div>
  );
}
