import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getHealth, type Health } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { cn } from "@/lib/utils";

type State = "ok" | "error" | "wait";

// jeden wiersz z nazwa uslugi i jej stanem
function Row({ label, state }: { label: string; state: State }) {
  const { t } = useTranslation();
  return (
    <li className="flex items-center gap-3 border-b border-dashed border-line py-3 last:border-b-0">
      <span
        className={cn(
          "size-3",
          state === "ok" && "bg-ok",
          state === "error" && "bg-bad",
          state === "wait" && "bg-mut",
        )}
      />
      <span className="flex-1">{label}</span>
      <span className={cn("pixel", state === "error" ? "text-bad" : "text-mut")}>
        {t(`health.${state}`)}
      </span>
    </li>
  );
}

// stan backendu, bazy i Redisa (strona pomocnicza /status)
export function HealthPage() {
  const { t } = useTranslation();
  const [health, setHealth] = useState<Health | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [loading, setLoading] = useState(true);

  // pyta backend o stan
  const load = useCallback(async () => {
    setLoading(true);
    try {
      setHealth(await getHealth());
      setApiDown(false);
    } catch {
      setHealth(null);
      setApiDown(true);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const api: State = loading ? "wait" : apiDown ? "error" : "ok";
  const db: State = loading ? "wait" : health?.db === "ok" ? "ok" : "error";
  const redis: State = loading ? "wait" : health?.redis === "ok" ? "ok" : "error";

  return (
    <section className="mx-auto flex max-w-xl flex-col border-t border-line pt-4">
      <h1 className="pixel mb-4 uppercase">{t("health.title")}</h1>
      <ul>
        <Row label={t("health.backend")} state={api} />
        <Row label={t("health.db")} state={db} />
        <Row label={t("health.redis")} state={redis} />
      </ul>
      <Button onClick={load} className="mt-5 self-start">
        <PixelIcon name="refresh" scale={1} />
        {t("health.retry")}
      </Button>
    </section>
  );
}
