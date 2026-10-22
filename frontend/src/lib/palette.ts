export const palettes = [
  { key: "grafit", name: "Grafit" },
  { key: "mosiadz", name: "Mosiądz" },
  { key: "rubin", name: "Rubin" },
];

export function getPalette() {
  return document.documentElement.dataset.palette ?? "grafit";
}

// ustawia palete kolorow na calej stronie
export function setPalette(key: string) {
  document.documentElement.dataset.palette = key;
}
