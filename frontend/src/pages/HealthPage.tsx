import { useCallback, useEffect, useState } from "react";
import { getHealth, type Health } from "@/api/client";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { getPalette, palettes, setPalette } from "@/lib/palette";
import { cn } from "@/lib/utils";

type State = "ok" | "error" | "wait";

// jeden wiersz z nazwa uslugi i jej stanem
function Row({ label, state }: { label: string; state: State }) {
  const text = { ok: "działa", error: "nie odpowiada", wait: "sprawdzam" }[state];
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
      <span className={cn("pixel", state === "error" ? "text-bad" : "text-mut")}>{text}</span>
    </li>
  );
}

// strona startowa etapu 0: pokazuje, czy backend, baza i Redis dzialaja
export function HealthPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [loading, setLoading] = useState(true);
  const [palette, setActive] = useState(getPalette);

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

  // zmienia palete kolorow
  function changePalette(key: string) {
    setPalette(key);
    setActive(key);
  }

  const api: State = loading ? "wait" : apiDown ? "error" : "ok";
  const db: State = loading ? "wait" : health?.db === "ok" ? "ok" : "error";
  const redis: State = loading ? "wait" : health?.redis === "ok" ? "ok" : "error";

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col gap-8 px-4 py-12">
      <header className="flex items-center gap-3 text-acc">
        <PixelIcon name="anvil" scale={2} />
        <span className="font-pixel text-[24px] leading-none text-fg">QuizForge</span>
      </header>

      <section className="border-t border-line pt-4">
        <h1 className="pixel mb-4 uppercase">Stan systemu</h1>
        <ul>
          <Row label="Backend (FastAPI)" state={api} />
          <Row label="Baza danych (PostgreSQL)" state={db} />
          <Row label="Redis" state={redis} />
        </ul>
        <button
          onClick={load}
          className="mt-5 inline-flex items-center gap-2 border border-acc bg-acc px-4 py-2 font-bold text-accfg shadow-ring"
        >
          <PixelIcon name="refresh" scale={1} />
          Sprawdź ponownie
        </button>
      </section>

      <section className="border-t border-line pt-4">
        <h2 className="pixel mb-4 uppercase">Paleta</h2>
        <div className="flex flex-wrap gap-2">
          {palettes.map((p) => (
            <button
              key={p.key}
              onClick={() => changePalette(p.key)}
              aria-pressed={palette === p.key}
              className={cn(
                "border border-line bg-surf2 px-3 py-1.5 shadow-ring",
                palette === p.key && "border-acc text-acc",
              )}
            >
              {p.name}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
