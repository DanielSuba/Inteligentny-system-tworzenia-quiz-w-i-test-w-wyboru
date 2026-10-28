import { useTranslation } from "react-i18next";
import type { JobIn } from "@/api/generation";
import type { QType } from "@/api/quizzes";
import type { Model } from "@/api/security";
import { Field } from "@/components/ui/Field";
import { cn } from "@/lib/utils";

type Props = { form: JobIn; models: Model[]; onChange: (patch: Partial<JobIn>) => void };

const types: QType[] = ["single", "multi", "true_false", "open"];
const select =
  "w-full border border-line bg-surf2 px-3 py-2 text-fg shadow-ring outline-none focus:border-acc";

const chip = (on: boolean) =>
  cn("border px-3 py-1 text-sm", on ? "border-acc text-acc" : "border-line text-mut hover:text-fg");

// ustawienia generowania: model, strategia, liczba i typy pytan, trudnosc, jezyk, temperatura
export function GenSettings({ form, models, onChange }: Props) {
  const { t } = useTranslation(["generate", "quiz"]);
  const modelKey = `${form.provider}::${form.model}`;

  function toggleType(ty: QType) {
    const next = form.types.includes(ty) ? form.types.filter((x) => x !== ty) : [...form.types, ty];
    if (next.length) onChange({ types: next });
  }

  return (
    <div className="flex flex-col gap-4">
      <label className="flex flex-col gap-1.5 text-sm text-mut">
        {t("settings.model")}
        {models.length ? (
          <select
            value={modelKey}
            onChange={(e) => {
              const [provider, model] = e.target.value.split("::");
              onChange({ provider, model });
            }}
            className={select}
          >
            {models.map((m) => (
              <option key={`${m.provider}::${m.id}`} value={`${m.provider}::${m.id}`}>
                {m.name} ({t(`security:models.${m.source}`)})
              </option>
            ))}
          </select>
        ) : (
          <span className="text-bad">{t("settings.noModels")}</span>
        )}
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm text-mut">
          {t("settings.strategy")}
          <select
            value={form.strategy}
            onChange={(e) => onChange({ strategy: e.target.value as JobIn["strategy"] })}
            className={select}
          >
            <option value="few_shot">{t("settings.few_shot")}</option>
            <option value="zero_shot">{t("settings.zero_shot")}</option>
          </select>
        </label>
        <Field
          label={t("settings.count")}
          type="number"
          min={1}
          max={50}
          value={form.count}
          onChange={(e) =>
            onChange({ count: Math.min(50, Math.max(1, Number(e.target.value) || 1)) })
          }
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <span className="text-sm text-mut">{t("settings.types")}</span>
        <div className="flex flex-wrap gap-2">
          {types.map((ty) => (
            <button
              key={ty}
              aria-pressed={form.types.includes(ty)}
              onClick={() => toggleType(ty)}
              className={chip(form.types.includes(ty))}
            >
              {t(`quiz:types.${ty}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <span className="text-sm text-mut">{t("settings.difficulty")}</span>
        <div className="flex flex-wrap gap-2">
          {[0, 1, 2, 3].map((d) => (
            <button
              key={d}
              aria-pressed={form.difficulty === d}
              onClick={() => onChange({ difficulty: d })}
              className={chip(form.difficulty === d)}
            >
              {d === 0 ? t("settings.mixed") : t(`quiz:editor.diff${d}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm text-mut">
          {t("settings.language")}
          <select
            value={form.language}
            onChange={(e) => onChange({ language: e.target.value as "pl" | "en" })}
            className={select}
          >
            <option value="pl">Polski</option>
            <option value="en">English</option>
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="text-mut">
            {t("settings.temperature", { v: form.temperature.toFixed(1) })}
          </span>
          <input
            type="range"
            min={0}
            max={1.5}
            step={0.1}
            value={form.temperature}
            onChange={(e) => onChange({ temperature: Number(e.target.value) })}
            className="accent-[var(--acc)]"
          />
          <span className="text-mut">{t("settings.temperatureHint")}</span>
        </label>
      </div>
    </div>
  );
}
