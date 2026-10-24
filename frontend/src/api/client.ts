// blad z API: code to klucz tlumaczenia w errors.* (np. invalid_credentials)
export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string) {
    super(code);
    this.status = status;
    this.code = code;
  }
}

type Options = { method?: string; json?: unknown; form?: FormData };

function readCsrf(): string {
  const row = document.cookie.split("; ").find((c) => c.startsWith("qf_csrf="));
  return row ? decodeURIComponent(row.split("=")[1]) : "";
}

// wspolna funkcja do zapytan: JSON, ciasteczka sesji, naglowek CSRF, bledy jako ApiError
export async function api<T>(path: string, opts: Options = {}): Promise<T> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  } else if (opts.form) {
    body = opts.form;
  }
  const method = opts.method ?? (body ? "POST" : "GET");

  if (method !== "GET") {
    // ciasteczko CSRF ustawia backend przy pierwszym zapytaniu
    if (!readCsrf()) await fetch("/api/health").catch(() => null);
    headers["X-CSRF-Token"] = readCsrf();
  }

  let res: Response;
  try {
    res = await fetch("/api" + path, { method, headers, body, credentials: "same-origin" });
  } catch {
    throw new ApiError(0, "network_error");
  }
  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    let code = typeof detail === "string" ? detail : "server_error";
    if (res.status === 422 && Array.isArray(detail)) {
      // backend odrzucil adres e-mail (np. nieistniejaca domena), reszte zglaszamy ogolnie
      const badEmail = detail.some((d: { loc?: string[] }) => d.loc?.includes("email"));
      code = badEmail ? "invalid_email" : "validation_error";
    }
    throw new ApiError(res.status, code);
  }
  return data as T;
}

export type Health = {
  status: "ok" | "error";
  db: "ok" | "error";
  redis: "ok" | "error";
};

// pobiera stan backendu; 503 tez ma tresc, wiec czytamy JSON niezaleznie od kodu
export async function getHealth(): Promise<Health> {
  const res = await fetch("/api/health");
  return (await res.json()) as Health;
}
