import { useTranslation } from "react-i18next";
import { updateMe } from "@/api/me";
import { useAuth } from "@/hooks/useAuth";
import { locales, setLocale, type Locale } from "@/lib/locale";
import { cn } from "@/lib/utils";

// przelacznik PL / EN; zalogowanym zapisuje jezyk w profilu
export function LangSwitch() {
  const { i18n, t } = useTranslation();
  const { user, setUser } = useAuth();

  async function change(next: Locale) {
    setLocale(next);
    if (user) setUser(await updateMe({ locale: next }).catch(() => user));
  }

  return (
    <div role="group" aria-label={t("lang.label")} className="flex">
      {locales.map((l) => (
        <button
          key={l}
          onClick={() => change(l)}
          aria-pressed={i18n.language === l}
          title={t(`lang.${l}`)}
          className={cn(
            "border border-line px-2 py-1 font-pixel text-[12px] uppercase",
            i18n.language === l ? "border-acc text-acc" : "text-mut hover:text-fg",
          )}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
