import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { changePassword, updateMe } from "@/api/me";
import { LangSwitch } from "@/components/layout/LangSwitch";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { useAuth } from "@/hooks/useAuth";
import { errorText } from "@/lib/errors";
import { paletteAccent, palettes, setPalette, type Palette } from "@/lib/palette";
import { cn } from "@/lib/utils";
import * as check from "@/lib/validate";

const emptyPass = { current: "", next: "", next2: "" };

// ustawienia: wyglad, jezyk, haslo
export function SettingsPage() {
  const { t } = useTranslation(["profile", "common", "auth"]);
  const { user, setUser } = useAuth();
  const me = user!;
  const [pass, setPass] = useState(emptyPass);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  // zmienia palete od razu, potem zapisuje ja w profilu
  async function choosePalette(p: Palette) {
    setPalette(p);
    setUser(await updateMe({ palette: p }).catch(() => ({ ...me, palette: p })));
  }

  // zmiana hasla; po sukcesie inne urzadzenia sa wylogowane
  async function submitPass(e: FormEvent) {
    e.preventDefault();
    const found = check.onlyErrors({
      current: check.required(pass.current),
      next: check.password(pass.next),
      next2: check.same(pass.next, pass.next2),
    });
    setErrs(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    try {
      await changePassword(pass.current, pass.next);
      setPass(emptyPass);
      setMsg({ kind: "ok", text: t("settings.changed") });
    } catch (err) {
      setMsg({ kind: "error", text: errorText(err) });
    }
    setBusy(false);
  }

  const err = (key: string) => errs[key] && t(`auth:${errs[key]}`);

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-8">
      <h1 className="pixel uppercase">{t("settings.title")}</h1>

      <section className="flex flex-col gap-3 border-t border-line pt-5">
        <h2 className="pixel uppercase text-mut">{t("settings.look")}</h2>
        <div role="group" aria-label={t("common:palette.label")} className="flex flex-wrap gap-3">
          {palettes.map((p) => (
            <button
              key={p}
              onClick={() => choosePalette(p)}
              aria-pressed={me.palette === p}
              className={cn(
                "flex items-center gap-2 border bg-surf2 px-3 py-2 shadow-ring",
                me.palette === p ? "border-acc text-fg" : "border-line text-mut hover:text-fg",
              )}
            >
              <span className="size-3" style={{ background: paletteAccent[p] }} />
              {t(`common:palette.${p}`)}
            </button>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3 border-t border-line pt-5">
        <h2 className="pixel uppercase text-mut">{t("settings.language")}</h2>
        <LangSwitch />
      </section>

      <section className="flex flex-col gap-4 border-t border-line pt-5">
        <h2 className="pixel uppercase text-mut">{t("settings.account")}</h2>
        <p>
          <span className="text-mut">{t("settings.email")}: </span>
          {me.email}
        </p>
        <form onSubmit={submitPass} noValidate className="flex flex-col gap-4">
          <h3 className="font-bold">{t("settings.password")}</h3>
          <Field
            label={t("settings.current")}
            type="password"
            autoComplete="current-password"
            value={pass.current}
            onChange={(e) => setPass({ ...pass, current: e.target.value })}
            error={err("current")}
          />
          <Field
            label={t("settings.new")}
            type="password"
            autoComplete="new-password"
            value={pass.next}
            onChange={(e) => setPass({ ...pass, next: e.target.value })}
            hint={t("auth:hints.password")}
            error={err("next")}
          />
          <Field
            label={t("settings.repeat")}
            type="password"
            autoComplete="new-password"
            value={pass.next2}
            onChange={(e) => setPass({ ...pass, next2: e.target.value })}
            error={err("next2")}
          />
          {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
          <Button type="submit" busy={busy} className="self-start">
            {t("settings.change")}
          </Button>
        </form>
      </section>
    </div>
  );
}
