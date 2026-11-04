import type { CSSProperties } from "react";
import { answerColor, letters, shapes } from "@/components/quiz/answerLook";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { cn } from "@/lib/utils";

type Props = {
  i: number; // numer odpowiedzi: litera, kolor, ksztalt
  text: string;
  picked: boolean;
  revealed: boolean;
  good: boolean; // po ujawnieniu: poprawna odpowiedz
  onClick: () => void;
};

// przycisk odpowiedzi (podglad quizu i nauka): ksztalt, kolor, litera; po ujawnieniu zielony/czerwony
export function AnswerButton({ i, text, picked, revealed, good, onClick }: Props) {
  const isGood = revealed && good;
  const isBad = revealed && picked && !good;
  return (
    <button
      onClick={onClick}
      aria-pressed={picked}
      disabled={revealed}
      className={cn(
        "flex items-center gap-3 border bg-surf2 px-4 py-3 text-left text-lg shadow-ring transition-colors",
        picked && !revealed ? "border-acc" : "border-line",
        !revealed && "hover:border-[color:var(--c)]",
        isGood && "border-ok bg-[color-mix(in_srgb,var(--ok)_18%,var(--surf2))]",
        isBad && "border-bad bg-[color-mix(in_srgb,var(--bad)_18%,var(--surf2))]",
        revealed && !isGood && !isBad && "text-mut",
      )}
      style={{ "--c": answerColor(i) } as CSSProperties}
    >
      <span style={{ color: answerColor(i) }}>
        <PixelIcon name={shapes[i]} scale={3} />
      </span>
      <span className="flex-1">{text}</span>
      {isGood && (
        <span className="text-ok">
          <PixelIcon name="check" scale={1} />
        </span>
      )}
      <span className="font-pixel text-[12px] text-mut">{letters[i]}</span>
    </button>
  );
}
