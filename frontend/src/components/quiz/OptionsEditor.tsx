import { useTranslation } from "react-i18next";
import type { Option, QType } from "@/api/quizzes";
import { answerColor, letters, shapes } from "@/components/quiz/answerLook";
import { PixelIcon } from "@/components/ui/PixelIcon";

const MAX = 10;

type Props = { type: QType; options: Option[]; onChange: (o: Option[]) => void };

// lista odpowiedzi do wyboru: tekst, znacznik poprawnej, dodawanie i usuwanie (2-10)
export function OptionsEditor({ type, options, onChange }: Props) {
  const { t } = useTranslation("quiz");
  const fixed = type === "true_false";

  // zaznacza poprawna odpowiedz (przy jednokrotnym wyborze tylko jedna)
  function mark(i: number) {
    onChange(
      options.map((o, j) =>
        type === "multi"
          ? j === i
            ? { ...o, isCorrect: !o.isCorrect }
            : o
          : { ...o, isCorrect: j === i },
      ),
    );
  }

  const setText = (i: number, text: string) =>
    onChange(options.map((o, j) => (j === i ? { ...o, text } : o)));

  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm text-mut">{t("editor.options")}</legend>
      {options.map((o, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="grid w-6 shrink-0 place-items-center" style={{ color: answerColor(i) }}>
            <PixelIcon name={shapes[i]} scale={2} />
          </span>
          <label className="flex shrink-0 cursor-pointer items-center gap-1.5 text-sm text-mut">
            <input
              type={type === "multi" ? "checkbox" : "radio"}
              name="correct"
              checked={o.isCorrect}
              onChange={() => mark(i)}
              className="size-4 accent-[var(--ok)]"
              aria-label={`${t("editor.correct")}: ${letters[i]}`}
            />
            <span className="font-pixel text-[12px]">{letters[i]}</span>
          </label>
          <input
            value={o.text}
            onChange={(e) => setText(i, e.target.value)}
            readOnly={fixed}
            maxLength={200}
            aria-label={t("editor.option", { letter: letters[i] })}
            className="min-w-0 flex-1 border border-line bg-surf2 px-3 py-2 shadow-ring outline-none focus:border-acc read-only:text-mut"
          />
          {!fixed && options.length > 2 && (
            <button
              onClick={() => onChange(options.filter((_, j) => j !== i))}
              aria-label={t("editor.removeOption", { letter: letters[i] })}
              className="p-2 text-mut hover:text-bad"
            >
              <PixelIcon name="close" scale={1} />
            </button>
          )}
        </div>
      ))}
      {!fixed && options.length < MAX && (
        <button
          onClick={() => onChange([...options, { text: "", isCorrect: false }])}
          className="self-start px-1 py-1 text-sm text-acc hover:underline"
        >
          + {t("editor.addOption")}
        </button>
      )}
    </fieldset>
  );
}
