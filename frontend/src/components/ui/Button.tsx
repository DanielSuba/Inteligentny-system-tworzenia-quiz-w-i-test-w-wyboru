import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  busy?: boolean;
};

const styles = {
  primary: "border-acc bg-acc text-accfg hover:brightness-110",
  secondary: "border-line bg-surf2 text-fg hover:border-acc",
  ghost: "border-transparent bg-transparent text-mut shadow-none hover:text-fg",
};

// przycisk w stylu aplikacji: ostre rogi, cien wokol; busy blokuje podwojne klikniecie
export function Button({
  variant = "primary",
  busy,
  className,
  disabled,
  children,
  ...rest
}: Props) {
  return (
    <button
      {...rest}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={cn(
        "inline-flex items-center justify-center gap-2 border px-4 py-2 font-bold shadow-ring",
        "transition-[filter,border-color,color] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acc",
        "disabled:cursor-not-allowed disabled:opacity-60",
        styles[variant],
        className,
      )}
    >
      {children}
    </button>
  );
}
