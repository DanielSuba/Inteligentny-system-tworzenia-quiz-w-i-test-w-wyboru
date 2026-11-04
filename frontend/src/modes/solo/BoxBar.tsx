import { useTranslation } from "react-i18next";
import type { LearnStats } from "@/api/learn";
import { boxColor } from "@/modes/solo/boxColor";

// pasek postepu: ile pytan w kazdym pudelku + procent opanowania
export function BoxBar({ stats }: { stats: LearnStats }) {
  const { t } = useTranslation("learn");
  const total = stats.total || 1;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="pixel uppercase text-mut">{t("bar.title")}</span>
        <span className="font-pixel text-[16px] text-acc">
          {t("bar.mastered", { pct: stats.masteredPct })}
        </span>
      </div>
      <div
        className="flex h-3 gap-0.5"
        role="img"
        aria-label={t("bar.aria", {
          boxes: stats.boxes.map((n, b) => `${t(`bar.box${b}`)}: ${n}`).join(", "),
        })}
      >
        {stats.boxes.map((n, b) =>
          n ? (
            <i key={b} style={{ flexGrow: n / total, background: boxColor[b] }} className="block" />
          ) : null,
        )}
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-mut">
        {stats.boxes.map((n, b) => (
          <li key={b} className="flex items-center gap-1.5">
            <i className="block size-2.5" style={{ background: boxColor[b] }} />
            {t(`bar.box${b}`)}: <span className="text-fg">{n}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
