import type { Media } from "@/api/media";

// 65 -> "1:05"
export const fmtTime = (s: number) =>
  `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

// "1:05" albo "65" -> 65 sekund; puste -> null; zly zapis -> NaN
export function parseTime(v: string): number | null {
  const s = v.trim();
  if (!s) return null;
  const m = s.match(/^(\d+):([0-5]?\d)$/);
  if (m) return Number(m[1]) * 60 + Number(m[2]);
  return /^\d+$/.test(s) ? Number(s) : NaN;
}

// czy gracz ma tylko slyszec (bez obrazu i tytulu z serwisu)
export const isHiddenMusic = (m: Media) =>
  m.kind === "audio" &&
  (m.source === "soundcloud" || m.source === "spotify" || (m.source === "youtube" && m.hideVideo));
