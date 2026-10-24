import { cn } from "@/lib/utils";

type Props = { url: string | null; name: string; size?: number; className?: string };

// avatar w kwadratowej ramce; bez obrazu pokazuje pierwsza litere nazwy
export function Avatar({ url, name, size = 32, className }: Props) {
  const style = { width: size, height: size };
  if (url) {
    return (
      <img
        src={url}
        alt=""
        style={style}
        className={cn("border border-line object-cover shadow-ring", className)}
      />
    );
  }
  return (
    <span
      style={style}
      aria-hidden="true"
      className={cn(
        "grid place-items-center bg-acc font-pixel text-accfg uppercase shadow-ring",
        size >= 64 ? "text-[24px]" : "text-[12px]",
        className,
      )}
    >
      {name.slice(0, 1)}
    </span>
  );
}
