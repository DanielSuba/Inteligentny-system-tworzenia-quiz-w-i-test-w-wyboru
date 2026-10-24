export const palettes = ["grafit", "mosiadz", "rubin"] as const;
export type Palette = (typeof palettes)[number];

// kolor akcentu kazdej palety (do probek w ustawieniach)
export const paletteAccent: Record<Palette, string> = {
  grafit: "#f0883e",
  mosiadz: "#d4a646",
  rubin: "#e8364f",
};

const KEY = "qf_palette";

export function getPalette(): Palette {
  const now = document.documentElement.dataset.palette;
  return palettes.includes(now as Palette) ? (now as Palette) : "grafit";
}

// ustawia palete kolorow na calej stronie i zapamietuje wybor
export function setPalette(key: Palette) {
  document.documentElement.dataset.palette = key;
  try {
    localStorage.setItem(KEY, key);
  } catch {
    // brak dostepu do localStorage
  }
}
