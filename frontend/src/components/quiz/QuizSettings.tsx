import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import {
  deleteQuiz,
  newShareToken,
  updateQuiz,
  type QuizDetail,
  type Visibility,
} from "@/api/quizzes";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";

const visibilities: Visibility[] = ["private", "unlisted", "public", "friends"];

type Props = { quiz: QuizDetail; onSaved: (q: QuizDetail) => void };

const select =
  "w-full border border-line bg-surf2 px-3 py-2 text-fg shadow-ring outline-none focus:border-acc";

// ustawienia quizu: tytul, opis, jezyk, widocznosc, tagi, link, usuwanie
export function QuizSettings({ quiz, onSaved }: Props) {
  const { t } = useTranslation("quiz");
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: quiz.title,
    description: quiz.description,
    language: quiz.language,
    visibility: quiz.visibility,
    tags: quiz.tags.join(", "),
  });
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);
  const [busy, setBusy] = useState(false);

  const link = `${window.location.origin}/share/${quiz.shareToken}`;
  const linkWorks = quiz.visibility === "public" || quiz.visibility === "unlisted";

  // zapisuje ustawienia quizu
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!form.title.trim()) return;
    setBusy(true);
    try {
      const tags = form.tags
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean);
      onSaved(await updateQuiz(quiz.id, { ...form, title: form.title.trim(), tags }));
      setMsg({ kind: "ok", text: t("common:saved") });
    } catch (err) {
      setMsg({ kind: "error", text: errorText(err) });
    }
    setBusy(false);
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  async function remove() {
    await deleteQuiz(quiz.id);
    navigate("/quizzes");
  }

  return (
    <form onSubmit={save} noValidate className="flex flex-col gap-4">
      <Field
        label={t("settings.name")}
        value={form.title}
        maxLength={120}
        onChange={(e) => setForm({ ...form, title: e.target.value })}
        error={form.title.trim() ? undefined : t("auth:validation.required")}
      />
      <Field
        multiline
        label={t("settings.description")}
        value={form.description}
        maxLength={1000}
        onChange={(e) => setForm({ ...form, description: e.target.value })}
      />
      <div className="grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-1.5 text-sm text-mut">
          {t("settings.language")}
          <select
            value={form.language}
            onChange={(e) => setForm({ ...form, language: e.target.value as "pl" | "en" })}
            className={select}
          >
            <option value="pl">Polski</option>
            <option value="en">English</option>
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm text-mut">
          {t("visibility.label")}
          <select
            value={form.visibility}
            onChange={(e) => setForm({ ...form, visibility: e.target.value as Visibility })}
            className={select}
          >
            {visibilities.map((v) => (
              <option key={v} value={v}>
                {t(`visibility.${v}`)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {form.visibility === "friends" && (
        <p className="text-sm text-mut">{t("visibility.friendsHint")}</p>
      )}
      <Field
        label={t("settings.tags")}
        value={form.tags}
        onChange={(e) => setForm({ ...form, tags: e.target.value })}
        hint={t("settings.tagsHint")}
      />
      {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
      <Button type="submit" busy={busy} className="self-start">
        {t("settings.save")}
      </Button>

      <div className="flex flex-col gap-2 border-t border-line pt-4">
        <span className="text-sm text-mut">{t("settings.share")}</span>
        <div className="flex gap-2">
          <input
            readOnly
            value={link}
            aria-label={t("settings.share")}
            className={`${select} min-w-0 text-sm`}
          />
          <Button type="button" variant="secondary" onClick={copy}>
            {copied ? t("settings.copied") : t("settings.copy")}
          </Button>
        </div>
        {!linkWorks && <p className="text-sm text-mut">{t("settings.shareOff")}</p>}
        <button
          type="button"
          onClick={async () => onSaved(await newShareToken(quiz.id))}
          className="self-start text-sm text-mut hover:text-fg"
          title={t("settings.newLinkHint")}
        >
          {t("settings.newLink")}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-line pt-4">
        {confirmDel ? (
          <>
            <span className="text-sm">{t("settings.deleteConfirm")}</span>
            <Button
              type="button"
              variant="secondary"
              className="border-bad text-bad"
              onClick={remove}
            >
              {t("settings.deleteYes")}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setConfirmDel(false)}>
              {t("settings.cancel")}
            </Button>
          </>
        ) : (
          <Button
            type="button"
            variant="ghost"
            className="px-0 hover:text-bad"
            onClick={() => setConfirmDel(true)}
          >
            {t("settings.delete")}
          </Button>
        )}
      </div>
    </form>
  );
}
