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
