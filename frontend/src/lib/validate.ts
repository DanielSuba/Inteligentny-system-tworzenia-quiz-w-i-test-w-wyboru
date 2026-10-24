// proste sprawdzanie pol formularzy; zwraca klucz tlumaczenia bledu albo null
export type Check = string | null;

export function required(v: string): Check {
  return v.trim() ? null : "validation.required";
}

export function email(v: string): Check {
  if (!v.trim()) return "validation.required";
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? null : "validation.email";
}

export function password(v: string): Check {
  if (!v) return "validation.required";
  return v.length >= 10 ? null : "validation.passwordShort";
}

export function same(a: string, b: string): Check {
  return a === b ? null : "validation.passwordMatch";
}

export function username(v: string): Check {
  if (!v.trim()) return "validation.required";
  return /^[A-Za-z0-9_]{3,24}$/.test(v) ? null : "validation.username";
}

// zostawia tylko pola z bledem
export function onlyErrors<T extends Record<string, Check>>(
  all: T,
): Partial<Record<keyof T, string>> {
  return Object.fromEntries(Object.entries(all).filter(([, v]) => v)) as Partial<
    Record<keyof T, string>
  >;
}
