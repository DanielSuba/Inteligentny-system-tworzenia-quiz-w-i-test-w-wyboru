import type { ReactNode } from "react";

type Props = { title: string; children: ReactNode; footer?: ReactNode };

// waska kolumna dla formularzy kont (logowanie, rejestracja, reset)
export function FormPage({ title, children, footer }: Props) {
  return (
    <section className="mx-auto flex max-w-sm flex-col gap-5 border-t border-line pt-5">
      <h1 className="pixel uppercase">{title}</h1>
      {children}
      {footer && <div className="flex flex-col gap-1 text-sm text-mut">{footer}</div>}
    </section>
  );
}
