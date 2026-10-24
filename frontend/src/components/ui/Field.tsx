import { useId, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Base = { label: string; error?: string; hint?: string };
type InputProps = Base & InputHTMLAttributes<HTMLInputElement> & { multiline?: false };
type AreaProps = Base & TextareaHTMLAttributes<HTMLTextAreaElement> & { multiline: true };

const box =
  "w-full border bg-surf2 px-3 py-2 text-fg shadow-ring outline-none placeholder:text-mut focus:border-acc";

// pole formularza z etykieta, podpowiedzia i bledem
export function Field(props: InputProps | AreaProps) {
  const id = useId();
  const { label, error, hint } = props;
  const describe = error ? `${id}-err` : hint ? `${id}-hint` : undefined;
  const look = cn(box, error ? "border-bad" : "border-line");

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm text-mut">
        {label}
      </label>
      {props.multiline ? (
        <textarea
          {...strip(props)}
          id={id}
          aria-invalid={!!error}
          aria-describedby={describe}
          className={cn(look, "min-h-24 resize-y")}
        />
      ) : (
        <input
          {...strip(props)}
          id={id}
          aria-invalid={!!error}
          aria-describedby={describe}
          className={look}
        />
      )}
      {error ? (
        <p id={`${id}-err`} className="text-sm text-bad">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-sm text-mut">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

// usuwa wlasne propsy, zeby nie trafily do elementu HTML
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function strip(props: any) {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { label, error, hint, multiline, ...rest } = props;
  return rest;
}
