import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import {
  addQuestion,
  deleteQuestion,
  duplicateQuestion,
  getQuiz,
  reorderQuestions,
  updateQuestion,
  type QType,
  type Question,
  type QuizDetail,
} from "@/api/quizzes";
import { emptyDraft, toDraft, toPayload, validate, type Draft } from "@/components/quiz/draft";
import { QuestionEditor } from "@/components/quiz/QuestionEditor";
import { QuestionList } from "@/components/quiz/QuestionList";
import { QuizSettings } from "@/components/quiz/QuizSettings";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";

const types: QType[] = ["single", "multi", "true_false", "open"];
type Msg = { kind: "ok" | "error"; text: string } | null;

// edytor quizu: ustawienia, lista pytan i formularz wybranego pytania
export function QuizEditorPage() {
  const { id = "" } = useParams();
  const { t } = useTranslation("quiz");
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [loadError, setLoadError] = useState("");
  const [draft, setDraft] = useState<Draft | null>(null);
  const [dirty, setDirty] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);
  const [saving, setSaving] = useState(false);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    getQuiz(id)
      .then(setQuiz)
      .catch((e) => setLoadError(errorText(e)));
  }, [id]);

  // przed porzuceniem zmian pyta uzytkownika
  const canLeave = () => !dirty || window.confirm(t("editor.discard"));

  function open(d: Draft | null) {
    if (!canLeave()) return;
    setDraft(d);
    setDirty(false);
    setMsg(null);
    setAdding(false);
    // na telefonie formularz jest pod lista, wiec przewijamy do niego
    if (d && window.innerWidth < 1024) {
      setTimeout(() => document.getElementById("question-editor")?.scrollIntoView(), 0);
    }
  }

  function edit(d: Draft) {
    setDraft(d);
    setDirty(true);
    setMsg(null);
  }

  // zamienia pytanie na liscie na nowa wersje z serwera
  function putQuestion(q: Question, afterId?: string) {
    setQuiz((cur) => {
      if (!cur) return cur;
      const list = cur.questions.filter((x) => x.id !== q.id);
      const at = afterId
        ? list.findIndex((x) => x.id === afterId) + 1
        : cur.questions.findIndex((x) => x.id === q.id);
      list.splice(at < 0 ? list.length : at, 0, q);
      return { ...cur, questions: list, questionCount: list.length };
    });
  }

  // zapisuje pytanie (nowe albo istniejace)
  async function save() {
    if (!draft || !quiz) return;
    const bad = validate(draft);
    if (bad) return setMsg({ kind: "error", text: t(bad) });
    setSaving(true);
    try {
      const q = draft.id
        ? await updateQuestion(draft.id, toPayload(draft))
        : await addQuestion(quiz.id, toPayload(draft));
      putQuestion(q);
      setDraft(toDraft(q));
      setDirty(false);
      setMsg({ kind: "ok", text: t("editor.saved") });
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
    setSaving(false);
  }

  async function duplicate() {
    if (!draft?.id || !canLeave()) return;
    const copy = await duplicateQuestion(draft.id);
    putQuestion(copy, draft.id);
    setDraft(toDraft(copy));
    setDirty(false);
  }

  async function remove() {
    if (!draft || !quiz) return;
    if (draft.id) await deleteQuestion(draft.id);
    const list = quiz.questions.filter((q) => q.id !== draft.id);
    setQuiz({ ...quiz, questions: list, questionCount: list.length });
    setDraft(null);
    setDirty(false);
  }

  // nowa kolejnosc: najpierw na ekranie, potem zapis na serwerze
  async function reorder(ids: string[]) {
    if (!quiz) return;
    const byId = new Map(quiz.questions.map((q) => [q.id, q]));
    setQuiz({ ...quiz, questions: ids.map((x) => byId.get(x)!) });
    try {
      setQuiz(await reorderQuestions(quiz.id, ids));
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  }

  if (loadError) return <Notice kind="error">{loadError}</Notice>;
  if (!quiz) return <p className="pixel text-mut">{t("common:loading")}</p>;

  const labels = { yes: t("editor.true"), no: t("editor.false") };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/quizzes" className="text-sm text-mut hover:text-fg">
          ← {t("settings.back")}
        </Link>
        <h1 className="mr-auto min-w-0 truncate text-xl font-bold">{quiz.title}</h1>
        <Link to={`/quizzes/${quiz.id}/preview`} className="text-sm text-acc hover:underline">
          {t("list.preview")}
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="flex flex-col gap-6">
          <section className="flex flex-col gap-3 border-t border-line pt-4">
            <h2 className="pixel uppercase text-mut">{t("editor.questions")}</h2>
            <QuestionList
              questions={quiz.questions}
              selected={draft?.id ?? null}
              newDraft={!!draft && !draft.id}
              onSelect={(qid) => open(toDraft(quiz.questions.find((q) => q.id === qid)!))}
              onReorder={reorder}
            />
            {adding ? (
              <div className="flex flex-wrap gap-2">
                {types.map((ty) => (
                  <Button key={ty} variant="secondary" onClick={() => open(emptyDraft(ty, labels))}>
                    {t(`types.${ty}`)}
                  </Button>
                ))}
              </div>
            ) : (
              <Button variant="secondary" className="self-start" onClick={() => setAdding(true)}>
                + {t("editor.add")}
              </Button>
            )}
          </section>
          <details className="border-t border-line pt-4">
            <summary className="pixel cursor-pointer uppercase text-mut hover:text-fg">
              {t("settings.title")}
            </summary>
            <div className="mt-4">
              <QuizSettings quiz={quiz} onSaved={setQuiz} />
            </div>
          </details>
        </div>

        <div id="question-editor" className="scroll-mt-4 border-t border-line pt-4">
          {draft ? (
            <QuestionEditor
              key={draft.id ?? "new"}
              draft={draft}
              onChange={edit}
              onSave={save}
              onDuplicate={duplicate}
              onDelete={remove}
              saving={saving}
              msg={msg}
            />
          ) : (
            <p className="text-mut">{t("editor.pick")}</p>
          )}
        </div>
      </div>
    </div>
  );
}
