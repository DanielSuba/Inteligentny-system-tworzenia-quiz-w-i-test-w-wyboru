import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/api/client";
import { addKey, deleteKey, stepUp, type ApiKey, type Provider } from "@/api/security";
import { CodePrompt } from "@/components/security/CodePrompt";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";

const providers: { key: Provider; name: string }[] = [
  { key: "openrouter", name: "OpenRouter" },
  { key: "openai", name: "OpenAI" },
  { key: "anthropic", name: "Anthropic" },
  { key: "google", name: "Google (Gemini)" },
];

type Props = { keys: ApiKey[]; twoFactor: boolean; onChanged: () => void };

const select =
  "w-full border border-line bg-surf2 px-3 py-2 text-fg shadow-ring outline-none focus:border-acc";

// lista kluczy i formularz; zmiany wymagaja potwierdzenia kodem (step-up)
export function ApiKeysSection({ keys, twoFactor, onChanged }: Props) {
  const { t, i18n } = useTranslation("security");
  const [provider, setProvider] = useState<Provider>("openrouter");
  const [label, setLabel] = useState("");
  const [raw, setRaw] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  // akcja czekajaca na potwierdzenie kodem
  const [pending, setPending] = useState<(() => Promise<void>) | null>(null);

  // wykonuje akcje; gdy serwer chce potwierdzenia, pokazuje pole na kod i ponawia
  async function guarded(action: () => Promise<void>) {
    setError("");
    try {
      await action();
    } catch (e) {
      if (e instanceof ApiError && e.code === "step_up_required") setPending(() => action);
      else setError(errorText(e));
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (raw.trim().length < 10) return;
    setBusy(true);
    await guarded(async () => {
      await addKey(provider, raw.trim(), label.trim());
      setRaw("");
      setLabel("");
      onChanged();
    });
    setBusy(false);
  }

  const date = (s: string) =>
    new Intl.DateTimeFormat(i18n.language, { dateStyle: "medium" }).format(new Date(s));

  return (
    <section className="flex flex-col gap-4 border-t border-line pt-5">
      <h2 className="pixel uppercase">{t("keys.title")}</h2>
      <p className="text-mut">{t("keys.lead")}</p>

      {keys.length === 0 ? (
        <p className="text-sm text-mut">{t("keys.none")}</p>
      ) : (
        <ul className="flex flex-col">
          {keys.map((k) => (
            <li
              key={k.id}
              className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-dashed border-line py-2"
            >
              <span className="font-bold">{k.label}</span>
              <span className="font-pixel text-[16px] text-mut">…{k.last4}</span>
              <span className="text-sm text-mut">
                {providers.find((p) => p.key === k.provider)?.name} ·{" "}
                {t("keys.added", { date: date(k.createdAt) })} ·{" "}
                {k.lastUsedAt ? t("keys.used", { date: date(k.lastUsedAt) }) : t("keys.neverUsed")}
              </span>
              <Button
                variant="ghost"
                className="ml-auto hover:text-bad"
                onClick={() =>
                  guarded(async () => {
                    await deleteKey(k.id);
                    onChanged();
                  })
                }
              >
                {t("keys.delete")}
              </Button>
            </li>
          ))}
        </ul>
      )}

      {pending && (
        <CodePrompt
          lead={t("stepUp.lead")}
          label={t("twoFactor.codeOrBackup")}
          submit={t("stepUp.submit")}
          onCancel={() => setPending(null)}
          onSubmit={async (code) => {
            await stepUp(code);
            const action = pending;
            setPending(null);
            await guarded(action);
          }}
        />
      )}

      {!twoFactor ? (
        <Notice kind="info">{t("keys.need2fa")}</Notice>
      ) : (
        <form onSubmit={submit} noValidate className="flex flex-col gap-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-sm text-mut">
              {t("keys.provider")}
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as Provider)}
                className={select}
              >
                {providers.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <Field
              label={t("keys.label")}
              maxLength={50}
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
          </div>
          <Field
            label={t("keys.key")}
            type="password"
            autoComplete="off"
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
          />
          {error && <Notice kind="error">{error}</Notice>}
          <Button
            type="submit"
            busy={busy}
            disabled={raw.trim().length < 10}
            className="self-start"
          >
            {t("keys.add")}
          </Button>
        </form>
      )}
    </section>
  );
}
