import { useTranslation } from "react-i18next";
import type { AuditEntry, Model } from "@/api/security";

// lista modeli dostepnych do generowania (wlasne klucze, systemowe, LM Studio)
export function ModelsSection({ models }: { models: Model[] }) {
  const { t } = useTranslation("security");
  return (
    <section className="flex flex-col gap-3 border-t border-line pt-5">
      <h2 className="pixel uppercase">{t("models.title")}</h2>
      <p className="text-mut">{t("models.lead")}</p>
      {models.length === 0 ? (
        <p className="text-sm text-mut">{t("models.none")}</p>
      ) : (
        <ul className="flex flex-col">
          {models.map((m) => (
            <li
              key={`${m.provider}/${m.id}`}
              className="flex flex-wrap gap-x-3 border-b border-dashed border-line py-2"
            >
              <span className="font-bold">{m.name}</span>
              <span className="text-sm text-mut">
                {t(`models.${m.source}`)}
                {m.context ? ` · ${t("models.context", { n: Math.round(m.context / 1000) })}` : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// ostatnie zdarzenia bezpieczenstwa
export function AuditSection({ entries }: { entries: AuditEntry[] }) {
  const { t, i18n } = useTranslation("security");
  const when = (s: string) =>
    new Intl.DateTimeFormat(i18n.language, { dateStyle: "medium", timeStyle: "short" }).format(
      new Date(s),
    );
  return (
    <section className="flex flex-col gap-3 border-t border-line pt-5">
      <h2 className="pixel uppercase">{t("audit.title")}</h2>
      {entries.length === 0 ? (
        <p className="text-sm text-mut">{t("audit.none")}</p>
      ) : (
        <ul className="flex flex-col text-sm">
          {entries.map((a, i) => (
            <li
              key={i}
              className="flex flex-wrap gap-x-3 border-b border-dashed border-line py-1.5"
            >
              <span>{t(`audit.${a.action}`, { defaultValue: a.action })}</span>
              {a.detail && <span className="text-mut">{a.detail}</span>}
              <span className="ml-auto text-mut">
                {when(a.createdAt)} · {a.ip}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
