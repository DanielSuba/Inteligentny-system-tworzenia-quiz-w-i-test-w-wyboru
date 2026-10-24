import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = { kind?: "ok" | "error" | "info"; children: ReactNode };

// komunikat pod formularzem; bledy sa ogloszone czytnikom ekranu
export function Notice({ kind = "info", children }: Props) {
  return (
    <div
      role={kind === "error" ? "alert" : "status"}
      className={cn(
        "border-l-4 bg-surf2 px-3 py-2 text-sm",
        kind === "ok" && "border-ok",
        kind === "error" && "border-bad",
        kind === "info" && "border-acc",
      )}
    >
      {children}
    </div>
  );
}
