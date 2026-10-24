import i18n from "i18next";

export const locales = ["pl", "en"] as const;
export type Locale = (typeof locales)[number];

const KEY = "qf_locale";

// jezyk zapamietany w przegladarce (dla gosci); domyslnie polski
export function getSavedLocale(): Locale {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "pl" || saved === "en") return saved;
  } catch {
    // brak dostepu do localStorage
  }
  return "pl";
}

// zmienia jezyk interfejsu i zapamietuje wybor
export function setLocale(locale: Locale) {
  i18n.changeLanguage(locale);
  document.documentElement.lang = locale;
  try {
    localStorage.setItem(KEY, locale);
  } catch {
    // brak dostepu do localStorage
  }
}
