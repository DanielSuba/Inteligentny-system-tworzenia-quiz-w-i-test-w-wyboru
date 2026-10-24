import { useTranslation } from "react-i18next";
import type { Draft } from "@/components/quiz/draft";
import { PixelIcon } from "@/components/ui/PixelIcon";

type Props = { draft: Draft; onChange: (patch: Partial<Draft>) => void };

// akceptowane warianty odpowiedzi otwartej i zasady sprawdzania
export function OpenAnswerEditor({ draft, onChange }: Props) {
  const { t } = useTranslation("quiz");
  const list = draft.accepted;
  const set = (i: number, v: string) =>
    onChange({ accepted: list.map((a, j) => (j === i ? v : a)) });

  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="mb-1 text-sm text-mut">{t("editor.accepted")}</legend>
      {list.map((a, i) => (
        <div key={i} className="flex items-center gap-2">
          <input
            value={a}
            maxLength={200}
            onChange={(e) => set(i, e.target.value)}
            aria-label={t("editor.variant", { n: i + 1 })}
            className="min-w-0 flex-1 border border-line bg-surf2 px-3 py-2 shadow-ring outline-none focus:border-acc"
          />
          {list.length > 1 && (
            <button
              onClick={() => onChange({ accepted: list.filter((_, j) => j !== i) })}
              aria-label={t("editor.removeVariant", { n: i + 1 })}
              className="p-2 text-mut hover:text-bad"
            >
              <PixelIcon name="close" scale={1} />
            </button>
          )}
        </div>
      ))}
      {list.length < 20 && (
        <button
          onClick={() => onChange({ accepted: [...list, ""] })}
          className="self-start px-1 py-1 text-sm text-acc hover:underline"
        >
          + {t("editor.addVariant")}
        </button>
      )}
      <p className="text-sm text-mut">{t("editor.acceptedHint")}</p>

      <label className="flex flex-col gap-1.5 text-sm">
        <span>{t("editor.fuzzy", { value: draft.fuzzyThreshold })}</span>
        <input
          type="range"
          min={50}
          max={100}
          step={5}
          value={draft.fuzzyThreshold}
          disabled={draft.caseSensitive}
          onChange={(e) => onChange({ fuzzyThreshold: Number(e.target.value) })}
          className="accent-[var(--acc)]"
        />
        <span className="text-mut">{t("editor.fuzzyHint")}</span>
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={draft.ignoreAccents}
          onChange={(e) => onChange({ ignoreAccents: e.target.checked })}
          className="size-4 accent-[var(--acc)]"
        />
        {t("editor.ignoreAccents")}
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={draft.caseSensitive}
          onChange={(e) => onChange({ caseSensitive: e.target.checked })}
          className="size-4 accent-[var(--acc)]"
        />
        {t("editor.caseSensitive")}
      </label>
    </fieldset>
  );
}
