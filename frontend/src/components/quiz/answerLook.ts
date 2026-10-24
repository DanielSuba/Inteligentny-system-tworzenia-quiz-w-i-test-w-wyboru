import type { IconName } from "@/components/ui/pixelIcons";

// kazda odpowiedz ma litere, kolor i ksztalt (rozroznialne tez dla daltonistow)
export const letters = "ABCDEFGHIJ";
export const shapes: IconName[] = [
  "tri",
  "dia",
  "cir",
  "sq",
  "star",
  "plus",
  "ring",
  "heart",
  "moon",
  "cross",
];

export function answerColor(i: number): string {
  return `var(--a${(i % 10) + 1})`;
}
