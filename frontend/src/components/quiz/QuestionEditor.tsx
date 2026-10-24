import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { QType } from "@/api/quizzes";
import { changeType, type Draft } from "@/components/quiz/draft";
import { MediaField } from "@/components/quiz/MediaField";
import { OpenAnswerEditor } from "@/components/quiz/OpenAnswerEditor";
import { OptionsEditor } from "@/components/quiz/OptionsEditor";
import { QuestionExtras } from "@/components/quiz/QuestionExtras";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { cn } from "@/lib/utils";

const types: QType[] = ["single", "multi", "true_false", "open"];

type Props = {
  draft: Draft;
  onChange: (d: Draft) => void;
  onSave: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  saving: boolean;
  msg: { kind: "ok" | "error"; text: string } | null;
};

// formularz jednego pytania
export function QuestionEditor({
  draft,
  onChange,
  onSave,
  onDuplicate,
  onDelete,
  saving,
  msg,
}: Props) {
  const { t } = useTranslation("quiz");
  const [confirmDel, setConfirmDel] = useState(false);
  const labels = { yes: t("editor.true"), no: t("editor.false") };
  const patch = (p: Partial<Draft>) => onChange({ ...draft, ...p });

  return (
    <section className="flex flex-col gap-5" aria-label={t("editor.text")}>
      <div role="group" aria-label={t("editor.type")} className="flex flex-wrap gap-2">
        {types.map((ty) => (
          <button
            key={ty}
            aria-pressed={draft.type === ty}
            onClick={() => onChange(changeType(draft, ty, labels))}
            className={cn(
              "border px-3 py-1.5 text-sm",
              draft.type === ty
                ? "border-acc bg-surf2 text-acc"
                : "border-line text-mut hover:text-fg",
            )}
          >
            {t(`types.${ty}`)}
          </button>
        ))}
      </div>

      <Field
        multiline
        label={t("editor.text")}
        value={draft.text}
        maxLength={500}
        onChange={(e) => patch({ text: e.target.value })}
      />

      <MediaField media={draft.media} onChange={(media) => patch({ media })} />

      {draft.type === "open" ? (
        <OpenAnswerEditor draft={draft} onChange={patch} />
      ) : (
        <OptionsEditor
          type={draft.type}
          options={draft.options}
          onChange={(options) => patch({ options })}
        />
      )}

      <Field
        multiline
        label={t("editor.explanation")}
        value={draft.explanation}
        maxLength={1000}
        hint={t("editor.explanationHint")}
        onChange={(e) => patch({ explanation: e.target.value })}
      />

      <QuestionExtras draft={draft} onChange={patch} />

      {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}

      <div className="flex flex-wrap items-center gap-2 border-t border-line pt-4">
        <Button onClick={onSave} busy={saving}>
          {t("editor.save")}
        </Button>
        {draft.id && (
          <Button variant="secondary" onClick={onDuplicate}>
            {t("editor.duplicate")}
          </Button>
        )}
        {confirmDel ? (
          <span className="flex items-center gap-2 text-sm">
            {t("editor.deleteConfirm")}
            <Button variant="secondary" className="border-bad text-bad" onClick={onDelete}>
              {t("settings.deleteYes")}
            </Button>
            <Button variant="ghost" onClick={() => setConfirmDel(false)}>
              {t("settings.cancel")}
            </Button>
          </span>
        ) : (
          <Button
            variant="ghost"
            className="ml-auto hover:text-bad"
            onClick={() => setConfirmDel(true)}
          >
            {t("editor.delete")}
          </Button>
        )}
      </div>
    </section>
  );
}
