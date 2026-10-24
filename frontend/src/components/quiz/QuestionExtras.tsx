import { useTranslation } from "react-i18next";
import type { Draft } from "@/components/quiz/draft";
import { Field } from "@/components/ui/Field";
import { cn } from "@/lib/utils";

type Props = { draft: Draft; onChange: (patch: Partial<Draft>) => void };

// dodatkowe ustawienia pytania: trudnosc, czas, punkty, kategoria
export function QuestionExtras({ draft, onChange }: Props) {
  const { t } = useTranslation("quiz");
  return (
    <details className="border-t border-line pt-3">
      <summary className="cursor-pointer text-sm text-mut hover:text-fg">
        {t("editor.more")}
      </summary>
      <div className="mt-3 flex flex-col gap-4">
        <div role="group" aria-label={t("editor.difficulty")} className="flex flex-col gap-1.5">
          <span className="text-sm text-mut">{t("editor.difficulty")}</span>
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3].map((d) => (
              <button
                key={d}
                aria-pressed={draft.difficulty === d}
                onClick={() => onChange({ difficulty: d })}
                className={cn(
                  "border px-3 py-1 text-sm",
                  draft.difficulty === d
                    ? "border-acc text-acc"
                    : "border-line text-mut hover:text-fg",
                )}
              >
                {t(`editor.diff${d}`)}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field
            label={t("editor.time")}
            type="number"
            min={5}
            max={300}
            value={draft.timeLimitS}
            onChange={(e) => onChange({ timeLimitS: e.target.value })}
            hint={t("editor.gameDefault")}
          />
          <Field
            label={t("editor.points")}
            type="number"
            min={0}
            max={10000}
            value={draft.points}
            onChange={(e) => onChange({ points: e.target.value })}
            hint={t("editor.gameDefault")}
          />
        </div>
        <Field
          label={t("editor.category")}
          maxLength={50}
          value={draft.category}
          onChange={(e) => onChange({ category: e.target.value })}
        />
      </div>
    </details>
  );
}
